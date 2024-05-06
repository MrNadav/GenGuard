# Real-Time Object Tracking with COCO-SSD and TensorFlow.js

## Background

This project demonstrates the use of TensorFlow.js to implement real-time object tracking in the browser. By leveraging the COCO-SSD model, it detects objects within the video stream captured from the user's webcam. Specifically, this implementation focuses on detecting and tracking a single object, prioritizing it based on movement.

The application is designed to detect movement using frame differencing techniques. Once movement is detected, the COCO-SSD model identifies objects within the frame. The system then tracks the largest object detected during movement, continuing to track it even if it momentarily stops moving.

## Features

- Real-time object detection and tracking in the browser
- Movement detection to initiate object tracking
- Continuous tracking of a single object, even if it stops moving
- Display of the object's class and confidence score

## How It Works

The application utilizes the webcam to capture video input. Each frame is analyzed for movement by comparing it with the previous frame. If significant movement is detected, the COCO-SSD model is invoked to identify objects within the current frame. Among the detected objects, the largest one is selected for tracking.

## Setup

To run this project locally, you need:

- Node.js installed on your system
- A modern web browser that supports TensorFlow.js and MediaDevices API

### Steps to Run

1. Clone the repository to your local machine.
2. Navigate to the project directory in your terminal.
3. Run `npm install` to install the required dependencies.
4. Start the server with `node server.js`.
5. Open your web browser and go to `http://localhost:3000`.

## Operating Instructions

1. Ensure your webcam is enabled and accessible.
2. Upon loading the application, grant permission to access your webcam.
3. The application will automatically start detecting and tracking objects in real-time.
4. The tracked object will be highlighted with a red bounding box, and its class and confidence score will be displayed.

## Technologies Used

- TensorFlow.js for running the COCO-SSD model in the browser
- Express.js for serving the application
- HTML5 and JavaScript for the frontend

## Contributions

Contributions are welcome! Please feel free to submit a pull request or open an issue for further enhancements or bug fixes.
