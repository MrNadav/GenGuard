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

# Initialize Firebase
cred = credentials.Certificate('fb/fb.json')  # Update with your actual file path
firebase_admin.initialize_app(cred, {
    'storageBucket': '',
    'databaseURL': ''
})
ref = db.reference('/esp/CAMIP')

video_stream_url = ''  # Initialize as empty

def fetch_esp_cam_ip():
    global video_stream_url
    url_db = ref.get(shallow=True)
    if not url_db:
        print("No IP address found")
        return

    print("Fetched ESP-CAM IP Address:", url_db)
    print("Type of fetched URL:", type(url_db))
    video_stream_url = url_db

fetch_esp_cam_ip()
print("Global video_stream_url:", video_stream_url)
# Configuration and Global Variables
frame_queue = queue.Queue(maxsize=15)
display_queue = queue.Queue(maxsize=15)  # Queue for frames to be displayed
phase_start = False
# Function to fetch frames from the camera
def fetch_frames():
    print("Starting Frame Fetching")
    cap = cv2.VideoCapture(video_stream_url)
    while True:
        ret, frame = cap.read()
        if not ret:
            #print('Failed to fetch frame')
            continue
        frame_queue.put(frame)

# Function to scan QR codes in the frame
def get_frame_and_scan_qr(frame):
    qr_detected = False
    user_id = None
    decoded_objects = decode(frame)
    for obj in decoded_objects:
        user_id = obj.data.decode('utf-8')
        qr_detected = True

        # Get the corners of the QR code
        points = obj.polygon
        if len(points) > 4 : 
            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
            points = hull
        n = len(points)

        # Draw the bounding box around the QR code
        for j in range(0,n):
            cv2.line(frame, points[j], points[ (j+1) % n], (255,0,0), 3)

        # Optionally, if you want to draw a rectangle instead of a polygon
        # rect = obj.rect
        # cv2.rectangle(frame, (rect.left, rect.top), (rect.left + rect.width, rect.top + rect.height), (255, 0, 0), 3)

        break  # Assuming you want to detect and highlight only one QR code per frame

    return frame, user_id, qr_detected

# Function to download reference image from Firebase
def download_reference_image(user_id):
    bucket = storage.bucket()
    blob = bucket.blob(f'user_photos/{user_id}.png')
    local_file_path = f'{user_id}.png'
    try:
        blob.download_to_filename(local_file_path)
        print(f"Downloaded {user_id}.png")
        return local_file_path
    except FileNotFoundError:
        print(f"File not found: {user_id}.png")
        return None

# Function to encode face using face_recognition library
def encode_face(face_image):
    rgb_img = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
    face_encodings = face_recognition.face_encodings(rgb_img)
    if face_encodings:
        return face_encodings[0]
    return None

# Function to perform face matching and return match percentage
def perform_face_matching(known_encoding, frame):
    match_percentage = 0
    best_match_percentage = 0
    best_match_location = None

    if known_encoding is None:
        return False, best_match_percentage, best_match_location

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        results = face_recognition.compare_faces([known_encoding], face_encoding)
        face_distance = face_recognition.face_distance([known_encoding], face_encoding)
        match_percentage = (1 - face_distance[0]) * 100

        if results[0] and match_percentage > best_match_percentage:
            best_match_percentage = match_percentage
            best_match_location = face_location

    return best_match_percentage > 51, best_match_percentage, best_match_location

# Function to display the frame
def display_frame(frame, user_id=None, match_percentage=0, match_location=None, access_granted=False):
    global phase_start
    if frame is None:
        print("Received invalid frame.")
        return
    elif user_id:
        phase_start = True
        cv2.putText(frame, f"User ID: {user_id}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        cv2.putText(frame, f"Match: {match_percentage:.2f}%", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        if match_location and match_percentage is not None:
            top, right, bottom, left = match_location
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"Match: {match_percentage:.2f}%", (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if(access_granted):
            cv2.putText(frame, f"Access Granted", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            


        else:
            cv2.putText(frame, f"Access Denied", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        


    elif match_location:
        pass
    if access_granted:
        #cv2.putText(frame, "Access Granted", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        print("granted")
    if(phase_start == False):
        cv2.putText(frame, "IDLE", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.imshow('Video Stream', frame)
    cv2.waitKey(1)

def process_frames():
    print("Starting Frame Processing")
    global phase_start
    while True:
        frame = frame_queue.get()
        try:
            _, user_id, qr_detected = get_frame_and_scan_qr(frame)
            access_granted = False
            match_percentage = 0
            match_location = None

            if qr_detected and user_id:
                print(f"QR Detected: {user_id}")
                local_image_path = download_reference_image(user_id)
                if local_image_path:
                    known_encoding = encode_face(cv2.imread(local_image_path))
                    start_time = time.time()
                    while time.time() - start_time < 10:  # Try for 10 seconds
                        frame = frame_queue.get()
                        match, match_percentage, match_location = perform_face_matching(known_encoding, frame)
                        if match:
                            access_granted = True
                            break
                        # Update the display info with each frame processed
                        display_info = {
                            "frame": frame,
                            "user_id": user_id,
                            "match_percentage": match_percentage,
                            "match_location": match_location,
                            "access_granted": access_granted
                        }
                        display_queue.put(display_info)

                    # Final display info after processing is complete
                    display_info = {
                        "frame": frame,
                        "user_id": user_id,
                        "match_percentage": match_percentage,
                        "match_location": match_location,
                        "access_granted": access_granted
                    }
                    display_queue.put(display_info)

                    if access_granted:
                        print(f"Access granted to {user_id}")
                        threading.Thread(target=handle_screenshot_and_upload, args=(frame, user_id, access_granted)).start()
                    else:
                        print("Face match failed, restarting QR scanning.")
                        threading.Thread(target=handle_screenshot_and_upload, args=(frame, user_id, access_granted)).start()

                else:
                    print(f"Failed to download the reference image for {user_id}.")
            else:
                # Put the frame back in the queue if no QR code is detected
                display_queue.put({"frame": frame})

        except Exception as e:
            print(f"Error in process_frames: {e}")
        phase_start = False


def display_frames():
    print("Starting Frame Display")
    cv2.namedWindow('Video Stream', cv2.WINDOW_AUTOSIZE)
    while True:
        display_info = display_queue.get()
        frame = display_info.get("frame")
        user_id = display_info.get("user_id")
        match_percentage = display_info.get("match_percentage")
        match_location = display_info.get("match_location")
        access_granted = display_info.get("access_granted")
        try:
            display_frame(frame, user_id, match_percentage, match_location, access_granted)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"Error in display_frames: {e}")






def handle_screenshot_and_upload(frame, user_id,access_granted):
    screenshot_filename = f"{user_id}_{access_granted}_{int(time.time())}.jpg"
    save_frame(frame, screenshot_filename)
    upload_to_firebase(screenshot_filename)
    if os.path.exists(screenshot_filename):
        os.remove(screenshot_filename)
        print(f"File {screenshot_filename} has been deleted.")
    else:
        print(f"The file {screenshot_filename} does not exist.")

def save_frame(frame, filename):
    cv2.imwrite(filename, frame)

def upload_to_firebase(filename):
    bucket = storage.bucket()
    blob = bucket.blob(f'logs/{filename}')
    blob.upload_from_filename(filename)
    print(f"Uploaded {filename} to Firebase Storage.")

def main():
    # Start threads
    fetch_thread = threading.Thread(target=fetch_frames, daemon=True)
    process_thread = threading.Thread(target=process_frames, daemon=True)
    display_thread = threading.Thread(target=display_frames,daemon=True)


    fetch_thread.start()
    process_thread.start()
    display_thread.start()

    # Wait for the display thread to finish before exiting
    display_thread.join()

if __name__ == '__main__':
    main()