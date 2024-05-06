from flask import Flask, Response, render_template
import cv2
import numpy as np
import serial
import firebase_admin
from firebase_admin import credentials, db
from threading import Thread
import time

# Firebase Setup
cred = credentials.Certificate('fb/fb.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': ''
})

app = Flask(__name__)

# Global variable to store the follow state
follow_state = False
esp_ip = None  # Variable to store the ESP IP address


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
        self.target_x = 90  # Initialize target position same as current position
        self.target_y = 90
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
            self.target_x = np.interp(center_x, [0, self.frame_shape[1]], [180, 0])
            self.target_y = np.interp(center_y, [0, self.frame_shape[0]], [0, 180])

        # Apply smoothing factor alpha to gradually move to the target position
        self.current_x = int(self.alpha * self.target_x + (1 - self.alpha) * self.current_x)
        self.current_y = int(self.alpha * self.target_y + (1 - self.alpha) * self.current_y)

        command = f"ServoX{int(self.current_x)}ServoY{int(self.current_y)}\n"
        if self.ser:
            self.ser.write(command.encode())
            time.sleep(0.1)

def detect_and_track():
    ser = get_serial_connection()
    video = cv2.VideoCapture(esp_ip + "/stream")
    backSub = cv2.createBackgroundSubtractorMOG2(varThreshold=50, detectShadows=True)
    last_x, last_y = 90, 90
    servo_controller = ServoController(ser, (720, 1280))  # Assume 720p as default

    while True:
        ret, frame = video.read()
        if not ret:
            break

        fgMask = backSub.apply(frame)
        _, thresh = cv2.threshold(fgMask, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            center_x = x + w // 2
            center_y = y + h // 2

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

            if follow_state:  # Use the cached follow state
                servo_controller.update_based_on_dead_zone(center_x, center_y)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


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
