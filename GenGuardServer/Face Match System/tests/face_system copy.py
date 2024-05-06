import cv2
import threading
import queue
import time
from pyzbar.pyzbar import decode
import firebase_admin
from firebase_admin import credentials, storage, db
import requests
import face_recognition
import numpy as np
import os
import cProfile
import websocket
from functools import lru_cache
import dlib

# Initialize Firebase
cred = credentials.Certificate('fb/fb.json')  # Update with your actual file path
firebase_admin.initialize_app(cred, {
    'storageBucket': '',
    'databaseURL': ''
})
ref = db.reference('/esp/CAMIP')
ref2 = db.reference('/esp/ESPIP')

alarm_state = False

epscamip = ''
video_stream_url = ''  # Initialize as empty
esp32_ip = ''

def fetch_ip():
    global video_stream_url, esp32_ip, epscamip
    url_db = ref.get(shallow=True)
    url_db2 = ref2.get(shallow=True)
    if not url_db and not url_db2:
        print("No IP address found")
        return

    print("Fetched ESP-CAM IP Address:", url_db)
    print("Fetched ESP32 IP Address:", url_db2)

    esp32_ip = url_db2
    epscamip = url_db
    video_stream_url = 'ws://' + url_db.split("//")[-1] + ":81" # Assuming epscamip is like "http://192.168.229.182"

fetch_ip()

print("Global video_stream_url:", video_stream_url)
print("ESP ip:", esp32_ip)

# Configuration and Global Variables
frame_queue = queue.Queue(maxsize=30)  # Increased queue size
display_queue = queue.Queue(maxsize=30)  # Increased queue size
phase_start = False
streaming_active = True

# Cached reference images
reference_image_cache = {}

# Initialize the face detector and face recognition model
detector = dlib.get_frontal_face_detector()
face_recognition_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")

def on_message(ws, message):
    nparr = np.frombuffer(message, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if not frame_queue.full():
        frame_queue.put(frame)

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print(f"### closed ### Code: {close_status_code}, Message: {close_msg}")

def fetch_frames():
    ws = websocket.WebSocketApp(video_stream_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

    try:
        while streaming_active:
            time.sleep(1)
    except KeyboardInterrupt:
        ws.close()

def get_frame_and_scan_qr(frame):
    qr_detected = False
    user_id = None
    decoded_objects = decode(frame)
    for obj in decoded_objects:
        user_id = obj.data.decode('utf-8')
        qr_detected = True
        cv2.rectangle(frame, (obj.rect.left, obj.rect.top), (obj.rect.left + obj.rect.width, obj.rect.top + obj.rect.height), (0, 255, 0), 2)
        break
    return frame, user_id, qr_detected

def download_reference_image(user_id):
    # Check if the file path is cached and the file exists.
    local_file_path = reference_image_cache.get(user_id)
    if local_file_path and os.path.exists(local_file_path):
        print(f"Using cached file for {user_id}")
        return local_file_path

    # Proceed to download the file if not found locally.
    bucket = storage.bucket()
    blob = bucket.blob(f'user_photos/{user_id}.png')
    local_file_path = f'{user_id}.png'

    try:
        blob.download_to_filename(local_file_path)
        print(f"Downloaded {user_id}.png")
        # Update the cache with the new file path.
        reference_image_cache[user_id] = local_file_path
        return local_file_path
    except FileNotFoundError:
        print(f"File not found on Firebase: {user_id}.png")
        # Optionally remove the entry from the cache if the file does not exist on Firebase.
        reference_image_cache.pop(user_id, None)
        return None

def encode_face(face_image):
    """
    Encode a face image to its corresponding encoding. Does not use caching directly on numpy arrays.
    """
    rgb_img = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
    face_encodings = face_recognition.face_encodings(rgb_img)
    if face_encodings:
        return face_encodings[0]  # Return the first encoding found
    return None

def perform_face_matching(known_encoding, frame, previous_locations):
    if known_encoding is None:
        print("No known encoding provided.")
        return [], previous_locations

    requests.get(esp32_ip + '/scanning')
    face_results = []
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    print(f"Detected {len(face_encodings)} faces")

    if not face_encodings:
        print("No faces found in the frame for matching.")
        return face_results, previous_locations

    for face_encoding, face_location in zip(face_encodings, face_locations):
        match = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.6)
        face_distance = face_recognition.face_distance([known_encoding], face_encoding)
        match_percentage = (1 - face_distance[0]) * 100
        print(f"Match: {match[0]}, Match Percentage: {match_percentage}")

        is_real = False
        if face_location in previous_locations:
            movement = np.linalg.norm(np.array(previous_locations.get(face_location, face_location)) - np.array(face_location))
            if movement > 10:
                is_real = True

        previous_locations[face_location] = face_location

        if match[0] and is_real:
            top, right, bottom, left = face_location
            face_results.append({
                "location": face_location,
                "match": True,
                "percentage": match_percentage,
                "is_real": is_real
            })
        else:
            print("Match failed or fake face detected.")

    return face_results, previous_locations

frame_count = 0
n = 20  # Process every 20th frame

def display_frame(frame, face_results, access_granted=False, user_id=None):
    if frame is None:
        print("Received invalid frame.")
        return

    global phase_start
    global alarm_state

    if alarm_state:
        cv2.putText(frame, "ALARM ACTIVATED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

    for result in face_results:
        top, right, bottom, left = result["location"]
        # Check if the face match was successful and if it was considered real
        if result.get("match") and result.get("is_real"):
           color = (0, 255, 0) if access_granted else (0, 0, 255)
           cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
           cv2.putText(frame, f"Match: {result['percentage']:.2f}%", (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
           print("Match and real face detected.")
        else:
           # Draw a red box for fake faces or when no match is found
           cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
           cv2.putText(frame, "Fake or No Match", (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
           print("Fake face or no match detected.")

    if user_id:
       phase_start = True
       cv2.putText(frame, f"User ID: {user_id}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
       if access_granted:
           cv2.putText(frame, "Access Granted", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
       else:
           cv2.putText(frame, "Access Denied", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    elif not phase_start:
       cv2.putText(frame, "IDLE", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.imshow('Video Stream', frame)
    cv2.waitKey(1)

def display_frames():
   print("Starting Frame Display")
   cv2.namedWindow('Video Stream', cv2.WINDOW_AUTOSIZE)
   while True:
       display_info = display_queue.get()
       frame = display_info.get("frame")
       message = display_info.get("message", "")
       if message:
           cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
       face_results = display_info.get("face_results", [])
       access_granted = display_info.get("access_granted")
       user_id = display_info.get("user_id")

       try:
           display_frame(frame, face_results, access_granted, user_id)
           if cv2.waitKey(1) & 0xFF == ord('q'):
               break
       except Exception as e:
           print(f"Error in display_frames: {e}")

def process_frames():
   print("Starting Frame Processing")
   global frame_count, phase_start
   last_not_permitted_time = 0
   cooldown_duration = 5
   previous_locations = {}  # Initialize here to ensure it's accessible

   requests.get(esp32_ip + '/idle')

   while True:
       if alarm_state:
           time.sleep(1)
           continue

       frame = frame_queue.get()
       current_time = time.time()

       try:
           if current_time - last_not_permitted_time > cooldown_duration:
               _, user_id, qr_detected = get_frame_and_scan_qr(frame)
               access_granted = False
               match_percentage = 0
               if qr_detected and user_id:
                   try:
                       local_image_path = download_reference_image(user_id)
                       print(f"QR Detected: {user_id}")
                       is_permit = fetch_is_permit(user_id)
                       if is_permit:
                           if local_image_path and os.path.exists(local_image_path):
                               known_encoding = encode_face(cv2.imread(local_image_path))
                               start_time = time.time()
                               toggle_led_and_control_stream()
                               while time.time() - start_time < 10 and not access_granted:
                                   frame = frame_queue.get()
                                   if frame_count % n == 0:
                                       face_results, previous_locations = perform_face_matching(known_encoding, frame, previous_locations)
                                   if face_results:  # Ensure there are results before processing them
                                       for result in face_results:
                                           if result["match"]:
                                               match_percentage = result["percentage"] + 20
                                               if match_percentage > 51 and not access_granted:
                                                   access_granted = True
                                                   display_info = {
                                                       "frame": frame,
                                                       "user_id": user_id,
                                                       "match_percentage": match_percentage,
                                                       "face_results": face_results,
                                                       "access_granted": access_granted
                                                   }
                                                   display_queue.put(display_info)
                                                   toggle_led_and_control_stream()
                                                   requests.get(esp32_ip + '/accessGranted')
                                                   handle_screenshot_and_upload(frame, user_id, access_granted)
                                                   break

                                   frame_count += 1
                                   display_info = {
                                       "frame": frame,
                                       "user_id": user_id,
                                       "match_percentage": match_percentage + 20,
                                       "face_results": face_results,
                                       "access_granted": access_granted
                                   }
                                   display_queue.put(display_info)
                               if not access_granted:
                                   print("Face match failed, restarting QR scanning.")
                                   requests.get(esp32_ip + '/accessDenied')
                                   handle_screenshot_and_upload(frame, user_id, access_granted)
                                   toggle_led_and_control_stream()
                           else:
                               print(f"Failed to download the reference image for {user_id}.")
                       else:
                           print(f"User {user_id} is not permitted.")
                           display_info = {"frame": frame, "message": "NOT PERMITTED"}
                           display_queue.put(display_info)
                           last_not_permitted_time = current_time
                           if os.path.exists(f"{user_id}.png"):
                               os.remove(f"{user_id}.png")
                           requests.get(esp32_ip + '/accessDenied')
                           time.sleep(1)
                   except Exception as e:
                       print(f"Exception processing user {user_id}: {e}")
                       display_info = {"frame": frame, "message": "INVALID QR detected"}
                       requests.get(esp32_ip + '/accessDenied')
                       display_queue.put(display_info)
                       last_not_permitted_time = current_time
                       if os.path.exists(f"{user_id}.png"):
                           os.remove(f"{user_id}.png")
                       time.sleep(1)
               else:
                   display_queue.put({"frame": frame})
                   requests.get(esp32_ip + '/idle')
       except Exception as e:
           print(f"Error in process_frames: {e}")

       phase_start = False
       frame_count = 0

def handle_screenshot_and_upload(frame, user_id, access_granted):
   screenshot_filename = f"{user_id}_{access_granted}_{int(time.time())}.jpg"
   save_frame(frame, screenshot_filename)
   upload_to_firebase_async(screenshot_filename)
# Delay before deletion
   time.sleep(1)

   try:
       if os.path.exists(screenshot_filename):
           os.remove(screenshot_filename)
           print(f"File {screenshot_filename} has been deleted.")
           os.remove(f"{user_id}.png")

   except Exception as e:
       print(f"Error deleting file {screenshot_filename}: {e}")

   print("end of handle_screenshot_and_upload")

def save_frame(frame, filename):
   cv2.imwrite(filename, frame)

def upload_to_firebase_async(filename):
   threading.Thread(target=upload_to_firebase, args=(filename,), daemon=True).start()

def upload_to_firebase(filename):
   bucket = storage.bucket()
   blob = bucket.blob(f'logs/{filename}')
   blob.upload_from_filename(filename)
   print(f"Uploaded {filename} to Firebase Storage.")

def toggle_led_and_control_stream():
   try:
       response = requests.get(f"{epscamip}/toggle-led")
       if response.status_code == 200:
           print("LED toggled")
       else:
           print("Failed to toggle LED")
   except Exception as e:
       print(f"Error toggling LED: {e}")

def fetch_is_permit(user_id):
   try:
       is_permit_ref = db.reference(f'users/{user_id}/isPermit')
       return is_permit_ref.get()
   except Exception as e:
       print(f"Error fetching /isPermit: {e}")
       return None

def listen_for_alarm_state():
   alarm_state_ref = db.reference('/Alarm/alarmState')

   def alarm_state_listener(event):
       global alarm_state
       alarm_state_value = event.data
       print(alarm_state_value)

       if isinstance(alarm_state_value, bool) and alarm_state_value:
           alarm_state = True
           print("Alarm is ACTIVE. System is idle.")
       elif str(alarm_state_value).lower() == "true":
           alarm_state = True
           print("Alarm is ACTIVE. System is idle.")
       else:
           alarm_state = False
           print("Alarm is INACTIVE. Resuming normal operations.")

   alarm_state_ref.listen(alarm_state_listener)

def main():
   # Start the alarm state listener
   alarm_state_listener_thread = threading.Thread(target=listen_for_alarm_state, daemon=True)
   alarm_state_listener_thread.start()

   # Start other threads
   fetch_thread = threading.Thread(target=fetch_frames, daemon=True)
   process_thread = threading.Thread(target=process_frames, daemon=True)
   display_thread = threading.Thread(target=display_frames, daemon=True)

   fetch_thread.start()
   process_thread.start()
   display_thread.start()

   # Wait for threads to finish before exiting
   display_thread.join()

if __name__ == '__main__':
   main()