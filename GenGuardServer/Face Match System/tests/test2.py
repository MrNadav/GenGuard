from flask import Flask, Response, render_template
import cv2
import numpy as np
import serial
import firebase_admin
from firebase_admin import credentials, db
from threading import Thread
import time
from sort import Sort
import torch

# Firebase Setup
cred = credentials.Certificate('fb/fb.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': ''
})

app = Flask(__name__)

# Global variable to store the follow state
follow_state = False
esp_ip = None  # Variable to store the ESP IP address

# Load YOLOv5 object detection model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5s.pt')
def update_follow_state():
    global follow_state, esp_ip
    while True:
        ref = db.reference('/Alarm/alarmState')
        follow_state_value = ref.get()
        if follow_state_value is not None:  # Check if the value is not None
            follow_state = str(follow_state_value).lower() == 'true'

        # Fetch ESP IP address
        esp_ref = db.reference('/esp/SECCAMIP')
        esp_ip = esp_ref.get()

        time.sleep(5)  # Update every 5 seconds


def get_serial_connection():
    try:
        ser = serial.Serial('COM3', 115200, timeout=1)
        return ser
    except serial.SerialException as e:
        print(f"Failed to connect to serial port: {e}")
        return None


# Servo Controller Class Definition
class ServoController:
    def __init__(self, ser, frame_shape, movement_threshold=25, step_size=5, dead_zone_factor=15, alpha=0.6):
        self.ser = ser
        self.frame_shape = frame_shape
        self.current_x = 90
        self.current_y = 90
        self.movement_threshold = movement_threshold
        self.step_size = step_size
        self.dead_zone_width = frame_shape[1] // dead_zone_factor
        self.dead_zone_height = frame_shape[0] // dead_zone_factor
        self.alpha = alpha  # Smoothing factor

    def update_based_on_dead_zone(self, center_x, center_y):
        frame_center_x, frame_center_y = self.frame_shape[1] // 2, self.frame_shape[0] // 2
        dx = center_x - frame_center_x
        dy = center_y - frame_center_y

        if abs(dx) > self.dead_zone_width // 2 or abs(dy) > self.dead_zone_height // 2:
            target_x = np.interp(center_x, [0, self.frame_shape[1]], [180, 0])
            target_y = np.interp(center_y, [0, self.frame_shape[0]], [0, 180])

            # Apply smoothing factor alpha to gradually move to the target position
            self.current_x = int(self.alpha * target_x + (1 - self.alpha) * self.current_x)
            self.current_y = int(self.alpha * target_y + (1 - self.alpha) * self.current_y)

            command = f"ServoX{int(self.current_x)}ServoY{int(self.current_y)}\n"
            if self.ser:
                self.ser.write(command.encode())
                time.sleep(0.1)

def detect_and_track():
    # Wait until esp_ip is initialized
    while esp_ip is None:
        time.sleep(0.5)  # Sleep briefly to wait for the update_follow_state thread to fetch the ESP IP address

    ser = get_serial_connection()
    video = cv2.VideoCapture(esp_ip + "/stream")
    video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set the desired width
    video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set the desired height
    backSub = cv2.createBackgroundSubtractorMOG2(varThreshold=50, detectShadows=True)
    tracker = Sort(max_age=5, min_hits=3)  # Initialize SORT tracker with max_age and min_hits
    servo_controller = ServoController(ser, (640, 480))  # Set frame shape

    prev_frame = None
    lk_params = {
        'winSize': (15, 15),
        'maxLevel': 4,
        'criteria': (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
    }

    while True:
        ret, frame = video.read()
        if not ret:
            break

        fgMask = backSub.apply(frame)
        _, thresh = cv2.threshold(fgMask, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            detections.append([x, y, x + w, y + h])

        if prev_frame is not None:
            old_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            new_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            p0 = cv2.goodFeaturesToTrack(old_gray, maxCorners=100, qualityLevel=0.3, minDistance=7, mask=None)

            if p0 is not None:
                p1, _, _ = cv2.calcOpticalFlowPyrLK(old_gray, new_gray, p0, None, **lk_params)
                for pt1, pt2 in zip(p0, p1):
                    if np.all(pt2[0] != 0):
                        x1, y1 = pt1.ravel()
                        x2, y2 = pt2.ravel()
                        if np.linalg.norm(pt2[0] - pt1[0]) > 1:  # Adjust this threshold as needed
                            detections.append([x1, y1, x2, y2])

        sort_input = np.array(detections, dtype=np.float64)

        # Update SORT tracker
        tracked_objects = tracker.update(sort_input)

        # Track only the object with the largest bounding box
        if tracked_objects:
            largest_object = max(tracked_objects, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))
            x1, y1, x2, y2, track_id = largest_object
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Center coordinates

            if follow_state:  # Use the cached follow state
                servo_controller.update_based_on_dead_zone(cx, cy)

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(frame, str(int(track_id)), (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        prev_frame = frame.copy()

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        

        
# def detect_and_track():
#     # Wait until esp_ip is initialized
#     while esp_ip is None:
#         time.sleep(0.5)  # Sleep briefly to wait for the update_follow_state thread to fetch the ESP IP address

#     ser = get_serial_connection()
#     video = cv2.VideoCapture(esp_ip + "/stream")
#     video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set the desired width
#     video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set the desired height
#     tracker = Sort()  # Initialize SORT tracker
#     servo_controller = ServoController(ser, (640, 480))  # Assume 720p as default

#     while True:
#         ret, frame = video.read()
#         if not ret:
#             break

#         # Detect objects using YOLOv5
#         results = model(frame)
#         detections = results.pandas().xyxy[0].to_numpy()

#         # Prepare the detections for SORT (converting to [x1, y1, x2, y2, confidence])
#         sort_input = detections[:, :4]  # Assuming your detections are in the format [x1, y1, x2, y2, confidence]
#         sort_input = np.array(sort_input, dtype=np.float64)

#         # Update SORT tracker
#         tracked_objects = tracker.update(sort_input)

#         # Draw bounding boxes and track IDs
#         for track in tracked_objects:
#             x1, y1, x2, y2, track_id = track
#             cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Center coordinates

#             if follow_state:  # Use the cached follow state
#                 servo_controller.update_based_on_dead_zone(cx, cy)

#             cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
#             cv2.putText(frame, str(int(track_id)), (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(detect_and_track(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    thread = Thread(target=update_follow_state)
    thread.daemon = True
    thread.start()
    app.run(host='0.0.0.0', debug=True)