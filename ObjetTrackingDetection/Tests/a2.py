import cv2
import numpy as np
import serial
import time
from filterpy.kalman import KalmanFilter


def update_pan_tilt_based_on_dead_zone(ser, bbox, frame_shape):
    frame_center_x, frame_center_y = frame_shape[1] // 2, frame_shape[0] // 2
    dead_zone_width, dead_zone_height = frame_shape[1] // 4, frame_shape[0] // 4  # Example dead zone size

    center_x = bbox[0] + bbox[2] / 2
    center_y = bbox[1] + bbox[3] / 2

    dx = center_x - frame_center_x
    dy = center_y - frame_center_y

    if abs(dx) > dead_zone_width // 2 or abs(dy) > dead_zone_height // 2:
        # Object is outside the dead zone; calculate new servo positions
        servo_x_pos = np.interp(center_x, [0, frame_shape[1]], [180, 0])
        servo_y_pos = np.interp(center_y, [0, frame_shape[0]], [0, 180])

        servo_x_pos = max(0, min(180, servo_x_pos))
        servo_y_pos = max(0, min(180, servo_y_pos))

        command = f"ServoX{int(servo_x_pos)}ServoY{int(servo_y_pos)}\n"
        ser.write(command.encode())

class ServoController:
    def __init__(self, ser, frame_shape, movement_threshold=15, step_size=5, dead_zone_factor=5):
        self.ser = ser
        self.frame_shape = frame_shape
        self.current_x = 90
        self.current_y = 90
        self.movement_threshold = movement_threshold
        self.step_size = step_size
        self.dead_zone_width = frame_shape[1] // dead_zone_factor
        self.dead_zone_height = frame_shape[0] // dead_zone_factor
        self.kalman_filter_x = KalmanFilter(dim_x=2, dim_z=1)
        self.kalman_filter_y = KalmanFilter(dim_x=2, dim_z=1)
        self.setup_kalman_filters()
    def setup_kalman_filters(self):
        for kf in [self.kalman_filter_x, self.kalman_filter_y]:
            kf.F = np.array([[1, 1], [0, 1]])  # State transition matrix
            kf.H = np.array([[1, 0]])          # Measurement function
            kf.P *= 1000.                       # Covariance matrix
            kf.R = 5                            # Measurement noise
            kf.Q = np.array([[1, 1], [1, 1]])   # Process noise

    def apply_kalman_filter(self, kf, measurement):
        kf.predict()
        kf.update(measurement)
        return kf.x[0]
    def update_based_on_dead_zone(self, center_x, center_y):
        frame_center_x, frame_center_y = self.frame_shape[1] // 2, self.frame_shape[0] // 2
        dx = center_x - frame_center_x
        dy = center_y - frame_center_y

        if abs(dx) > self.dead_zone_width // 2 or abs(dy) > self.dead_zone_height // 2:
            target_x = np.interp(center_x, [0, self.frame_shape[1]], [180, 0])
            target_y = np.interp(center_y, [0, self.frame_shape[0]], [0, 180])
            target_x = self.apply_kalman_filter(self.kalman_filter_x, target_x)
            target_y = self.apply_kalman_filter(self.kalman_filter_y, target_y)
            self.update(target_x, target_y)

    def update(self, target_x, target_y):
        dx = target_x - self.current_x
        dy = target_y - self.current_y

        # Debugging output
        print(f"Current X: {self.current_x}, Current Y: {self.current_y}")
        print(f"Delta X: {dx}, Delta Y: {dy}")

        if abs(dx) > self.movement_threshold or abs(dy) > self.movement_threshold:
            self.current_x += np.clip(dx, -self.step_size, self.step_size)
            self.current_y += np.clip(dy, -self.step_size, self.step_size)

            # Send command to the Arduino
            command = f"ServoX{int(self.current_x)}ServoY{int(self.current_y)}\n"
            ser.write(command.encode())

            # Debugging output
            print(f"Sent command: {command.strip()}")
            time.sleep(0.1)

def is_significant_motion_present(bbox, frame, background):
    if bbox is None:
        return False  # Early exit if bbox is None

    x, y, w, h = bbox
    # Ensure bbox is within frame bounds
    if w <= 0 or h <= 0 or x < 0 or y < 0 or (x+w) > frame.shape[1] or (y+h) > frame.shape[0]:
        return False

    roi_frame = frame[y:y+h, x:x+w]
    roi_background = background[y:y+h, x:x+w]

    if roi_frame.size == 0 or roi_background.size == 0:  # Check if ROI is empty
        return False

    fgmask = cv2.absdiff(roi_background, roi_frame)
    fgmask = cv2.cvtColor(fgmask, cv2.COLOR_BGR2GRAY)
    _, fgmask = cv2.threshold(fgmask, 25, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour_area = 0 if not contours else max(cv2.contourArea(cnt) for cnt in contours)
    return largest_contour_area > 100


def detect_moving_object(frame, background):
    fgmask = cv2.absdiff(background, frame)
    fgmask = cv2.cvtColor(fgmask, cv2.COLOR_BGR2GRAY)
    _, fgmask = cv2.threshold(fgmask, 50, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > 500:
            x, y, w, h = cv2.boundingRect(largest_contour)
            return (x, y, w, h)
    return None

def initialize_tracker(frame, bbox):
    tracker = cv2.TrackerCSRT_create()
    tracker.init(frame, bbox)
    return tracker

def update_pan_tilt(ser, bbox, frame_shape):
    center_x = bbox[0] + bbox[2] / 2
    center_y = bbox[1] + bbox[3] / 2

    servo_x_pos = np.interp(center_x, [0, frame_shape[1]], [180, 0])
    servo_y_pos = np.interp(center_y, [0, frame_shape[0]], [0, 180])  # Inverting direction

    servo_x_pos = max(0, min(180, servo_x_pos))
    servo_y_pos = max(0, min(180, servo_y_pos))

    command = f"ServoX{int(servo_x_pos)}ServoY{int(servo_y_pos)}\n"
    ser.write(command.encode())

# Setup serial connection
# Setup serial connection
try:
    ser = serial.Serial('COM3', 115200, timeout=1)  # Update 'COM3' to your Arduino's COM port
except serial.SerialException as e:
    print(f"Serial exception: {e}")
    exit()

video = cv2.VideoCapture("http://192.168.209.194/stream")
ret, frame = video.read()
if not ret:
    print("Failed to grab frame")
    video.release()
    cv2.destroyAllWindows()
    ser.close()
    exit()  # Ensure we exit if we cannot grab a frame

# Define frame_shape after successfully reading a frame
frame_shape = frame.shape
frame_center_x, frame_center_y = frame_shape[1] // 2, frame_shape[0] // 2
dead_zone_width, dead_zone_height = frame_shape[1] // 4, frame_shape[0] // 4

background = frame.copy()
tracker_initialized = False
tracker = None
servo_controller_initialized = False

# After this point, you can safely use frame_shape, frame_center_x, frame_center_y,
# dead_zone_width, and dead_zone_height as they are now defined.

while True:
    ret, frame = video.read()
    if not ret:
        break
    
    if not servo_controller_initialized:
        frame_shape = frame.shape  # Obtain frame_shape after you are sure you have a frame
        servo_controller = ServoController(ser, frame_shape)  # Instantiate ServoController with frame_shape
        servo_controller_initialized = True
        
    if not tracker_initialized:
        bbox = detect_moving_object(frame, background)
        if bbox:
            tracker = initialize_tracker(frame, bbox)
            tracker_initialized = True
            background = frame.copy()  # Update background to prevent immediate re-detection
    else:
        success, bbox = tracker.update(frame)
        if success:
            # Get the center of the bounding box
            center_x = bbox[0] + bbox[2] / 2
            center_y = bbox[1] + bbox[3] / 2
            
            # Update the servo position to point at the center of the detected object
            target_x = np.interp(center_x, [0, frame_shape[1]], [180, 0])
            target_y = np.interp(center_y, [0, frame_shape[0]], [0, 180])
            
            servo_controller.update(target_x, target_y)

            # If the object center is close enough to the frame center, recalculate the object position
            if abs(center_x - frame_center_x) < dead_zone_width // 2 and abs(center_y - frame_center_y) < dead_zone_height // 2:
                bbox = detect_moving_object(frame, background)  # Redetect to update bbox if needed
                
            if bbox:
                # Draw the updated bounding box on the frame
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                cv2.rectangle(frame, p1, p2, (255,0,0), 2)
                
            else:
                print("Object lost, reinitializing tracker...")
                tracker_initialized = False

        else:
            print("Tracking lost. Waiting for new object...")
            tracker_initialized = False
            time.sleep(0.5)  # A brief pause to stabilize

    cv2.imshow("Frame", frame)
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
ser.close()