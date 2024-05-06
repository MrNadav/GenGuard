import cv2
import numpy as np
import serial

def detect_moving_objects(video, count, frame_count, threshold, frames, initial, ser):
    images_old = None  # Initialize variable for previous frame storage
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break
        frames.append(frame)
        count += 1

        if count > frame_count:
            images = np.array(frames[count-frame_count: count])
            images_new = images.mean(axis=0)

            if not initial:
                diff = np.sum(np.abs(images_new - images_old), axis=2)
                _, diff = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
                diff = diff.astype(np.uint8)

                # Find contours of the moving objects
                contours, _ = cv2.findContours(diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    # Find the largest contour based on area
                    largest_contour = max(contours, key=cv2.contourArea)

                    # Check if the largest contour is above a certain size to reduce noise
                    if cv2.contourArea(largest_contour) > 500:  # Adjust 500 to your needs
                        x, y, w, h = cv2.boundingRect(largest_contour)
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                        # Calculate the center of the bounding box
                        center_x, center_y = x + w//2, y + h//2
                        cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                        print(f"Center of moving object: ({center_x}, {center_y})")
                        
                        # Send commands to ESP32 to control servos based on object position
                        command = f"ServoX{center_x}ServoY{center_y}\n"
                        ser.write(command.encode())

                cv2.imshow('Frame', frame)

            images_old = images_new.copy()  # Update the previous frame
            initial = False

            if cv2.waitKey(25) & 0xFF == ord('q'):
                break

# Change the video source to 0 for webcam
video = cv2.VideoCapture(0)

# Initialize serial communication with ESP32
ser = serial.Serial('COM3', 115200)  # Adjust to your ESP32's COM port
if not ser.is_open:
    ser.open()

count, frame_count, threshold, frames, initial = 0, 1, 100, [], True

detect_moving_objects(video, count, frame_count, threshold, frames, initial, ser)

video.release()
cv2.destroyAllWindows()
ser.close()
