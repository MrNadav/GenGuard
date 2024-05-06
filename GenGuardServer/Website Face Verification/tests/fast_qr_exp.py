import cv2
import threading
import queue
import time
from pyzbar.pyzbar import decode
import firebase_admin
from firebase_admin import credentials, storage

# Initialize Firebases
cred = credentials.Certificate('fb/fb.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': ''
})

# Replace with the URL of your video stream
video_stream_url = 'http://192.168.50.82/stream'
frame_queue = queue.Queue(maxsize=5)
processed_qr_codes = set()  # Set to keep track of processed QR codes
# Queue for storing frames

def fetch_frames():
    cap = cv2.VideoCapture(video_stream_url)
    while True:
        ret, frame = cap.read()
        if not ret:
            print('Failed to fetch frame')
            break
        if not frame_queue.full():  # Only add to queue if not full
            frame_queue.put(frame)
        else:
            time.sleep(0.01)  # Sleep briefly if the queue is full

def get_frame_and_scan_qr(frame):
    qr_detected = False
    user_id = None
    decoded_objects = decode(frame)
    for obj in decoded_objects:
        user_id = obj.data.decode('utf-8')
        if user_id not in processed_qr_codes:  # Check if QR code is new
            cv2.rectangle(frame, (obj.rect.left, obj.rect.top), (obj.rect.left + obj.rect.width, obj.rect.top + obj.rect.height), (0, 255, 0), 2)
            qr_detected = True
            processed_qr_codes.add(user_id)  # Mark QR code as processed
            break
    return frame, user_id, qr_detected

def download_reference_image(user_id):
    bucket = storage.bucket()
    blob = bucket.blob(f'user_photos/{user_id}.png')
    try:
        blob.download_to_filename(f'{user_id}.png')
        print(f"Downloaded {user_id}.png")
    except FileNotFoundError:
        print(f"File not found: {user_id}.png")

def download_reference_image_in_thread(user_id):
    # Function to be run in a thread for downloading images
    def download_thread():
        download_reference_image(user_id)

    # Start the download in a new thread
    threading.Thread(target=download_thread, daemon=True).start()

def display_frames():
    cv2.namedWindow('Video Stream', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Video Stream', 640, 480)

    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            frame, user_id, qr_detected = get_frame_and_scan_qr(frame)
            if qr_detected:
                # Start a thread for downloading the image
                download_reference_image_in_thread(user_id)
            cv2.imshow('Video Stream', frame)
            key = cv2.waitKey(1) & 0xFF
            # Press 'q' to exit the stream
            if key == ord('q'):
                break
        else:
            time.sleep(0.01)  # Sleep briefly if the queue is empty

    cv2.destroyAllWindows()

def main():
    # Start the frame fetching thread
    threading.Thread(target=fetch_frames, daemon=True).start()

    # Start the frame displaying function
    try:
        display_frames()
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    main()