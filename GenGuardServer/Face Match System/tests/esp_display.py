import cv2
import requests
import numpy as np

# Replace with the URL of your video stream
video_stream_url = 'http://192.168.1.101/stream'

def fetch_and_display_stream():
    cap = cv2.VideoCapture(video_stream_url)

    if not cap.isOpened():
        print('Failed to open video stream')
        return
    cv2.namedWindow('Video Stream', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Video Stream', 640, 480)

    while True:
        ret, frame = cap.read()
        if not ret:
            print('No frame captured')
            break

        cv2.imshow('Video Stream', frame)
        key = cv2.waitKey(1) & 0xFF

        # Press 'q' to exit the stream
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

try:
    fetch_and_display_stream()
except Exception as e:
    print('Error:', e)
