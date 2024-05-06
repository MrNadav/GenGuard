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

face_net = cv2.dnn.readNetFromCaffe('face-detection/deploy.prototxt', 'face-detection/res10_300x300_ssd_iter_140000.caffemodel')

# Initialize Firebase
cred = credentials.Certificate('fb/fb.json')  # Update with your actual file path
firebase_admin.initialize_app(cred, {
    'storageBucket': '',
    'databaseURL': ''
})
ref = db.reference('/esp/CAMIP')
ref2 = db.reference('/esp/ESPIP')

video_stream_url = ''  # Initialize as empty
esp32_ip = ''
def fetch_ip():
    global video_stream_url, esp32_ip
    url_db = ref.get(shallow=True)
    url_db2 = ref2.get(shallow=True)
    if not url_db and not url_db2:
        print("No IP address found")
        return

    print("Fetched ESP-CAM IP Address:", url_db)
    print("Fetched ESP32 IP Address:", url_db2)

    esp32_ip = url_db2
    video_stream_url = url_db

fetch_ip()
print("Global video_stream_url:", video_stream_url)
print("ESP ip:", esp32_ip)

# Configuration and Global Variables
frame_queue = queue.Queue(maxsize=15)
display_queue = queue.Queue(maxsize=15)  # Queue for frames to be displayed
phase_start = False
# Function to fetch frames from the camera
def fetch_frames():
    cap = cv2.VideoCapture(video_stream_url)
    while True:
        ret, frame = cap.read()
        if not ret:
            print('Failed to fetch frame')
            break
        frame = cv2.resize(frame, (640, 480))  # Resize the frame
        if not frame_queue.full():  # Only add to queue if not full
            frame_queue.put(frame)
        else:
            time.sleep(0.01)  # Sleep briefly if the queue is full

# Function to scan QR codes in the frame
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
    
def download_reference_image_in_thread(user_id):
    # Function to be run in a thread for downloading images
    def download_thread():
        download_reference_image(user_id)

    # Start the download in a new thread
    threading.Thread(target=download_thread, daemon=True).start()


# Function to encode face using face_recognition library
def encode_face(face_image):
    rgb_img = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
    face_encodings = face_recognition.face_encodings(rgb_img)
    if face_encodings:
        return face_encodings[0]
    return None

# Function to perform face matching and return match percentage

def perform_face_matching(known_encoding, frame):
    requests.get(esp32_ip+'/scanning')
    face_results = []

    if known_encoding is None:
        return face_results

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        match = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.6)
        face_distance = face_recognition.face_distance([known_encoding], face_encoding)
        match_percentage = (1 - face_distance[0]) * 100

        face_results.append({
            "location": face_location,
            "match": match[0],
            "percentage": match_percentage
        })

    return face_results

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

def display_frame(frame, face_results, access_granted=False):
    if frame is None:
        print("Received invalid frame.")
        return

    # Draw rectangles for all faces
    for result in face_results:
        top, right, bottom, left = result["location"]
        if result["match"]:
            # Known face - Draw in green or red depending on access_granted
            color = (0, 255, 0) if access_granted else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, f"Match: {result['percentage']:.2f}%", (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            # Other faces - Draw in a different color (e.g., blue)
            cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)

    if access_granted:
        cv2.putText(frame, "Access Granted", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "Access Denied", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imshow('Video Stream', frame)
    cv2.waitKey(1)

frame_count = 0
n = 10  # Process every 5th frame


def display_frame(frame, face_results, access_granted=False, user_id=None):
    if frame is None:
        print("Received invalid frame.")
        return

    global phase_start

    # Draw rectangles for all faces
    for result in face_results:
        top, right, bottom, left = result["location"]
        if result["match"]:
            # Known face - Draw in green or red depending on access_granted
            color = (0, 255, 0) if access_granted else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, f"Match: {result['percentage']:.2f}%", (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            # Other faces - Draw in blue
            cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)

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
        face_results = display_info.get("face_results", [])  # Use an empty list as default
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
    requests.get(esp32_ip+'/idle')
    while True:
        frame = frame_queue.get()
        try:
            _, user_id, qr_detected = get_frame_and_scan_qr(frame)
            access_granted = False
            match_percentage = 0

            if qr_detected and user_id:
                print(f"QR Detected: {user_id}")
                local_image_path = download_reference_image(user_id)
                if local_image_path:
                    known_encoding = encode_face(cv2.imread(local_image_path))
                    start_time = time.time()
                    while time.time() - start_time < 10 and access_granted == False:  # Try for 10 seconds
                        frame = frame_queue.get()
                        if frame_count % n == 0:
                            face_results = perform_face_matching(known_encoding, frame)
                            for result in face_results:
                                if result["match"]:
                                    match_percentage = result["percentage"]
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
                                        requests.get(esp32_ip+'/accessGranted')
                                        handle_screenshot_and_upload(frame, user_id, access_granted)
                                        break  # Break out of the loop immediately on access granted
                            
                        frame_count += 1

                        # Update the display for each frame processed
                        display_info = {
                            "frame": frame,
                            "user_id": user_id,
                            "match_percentage": match_percentage,
                            "face_results": face_results,
                            "access_granted": access_granted
                        }
                        display_queue.put(display_info)
        
                    if not access_granted:
                        print("Face match failed, restarting QR scanning.")
                        requests.get(esp32_ip+'/accessDenied')
                        handle_screenshot_and_upload(frame, user_id, access_granted)

                else:
                    print(f"Failed to download the reference image for {user_id}.")
            else:
                display_queue.put({"frame": frame})
                requests.get(esp32_ip+'/idle')  # Call idle when no QR code is detected


        except Exception as e:
            print(f"Error in process_frames: {e}")
        phase_start = False
        frame_count = 0  # Reset frame count for next user


def handle_screenshot_and_upload(frame, user_id, access_granted):
    screenshot_filename = f"{user_id}_{access_granted}_{int(time.time())}.jpg"
    save_frame(frame, screenshot_filename)
    upload_to_firebase(screenshot_filename)

    # Delay before deletion
    time.sleep(1)  # Delay for 1 second

    # Exception handling during deletion
    try:
        if os.path.exists(screenshot_filename):
            os.remove(screenshot_filename)
            print(f"File {screenshot_filename} has been deleted.")
    except Exception as e:
        print(f"Error deleting file {screenshot_filename}: {e}")
    print("end of handle_screenshot_and_upload")
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
    cProfile.run("main()", sort="cumulative")