# GenGuard
![Project Model](https://github.com/MrNadav/GenGuard/assets/72983086/70767e45-d806-4879-b81b-74ae04bc6d68)

(MFA) is implemented to improve access control security in various organizations. Each user is required to create an account and upload a profile picture of their face. This image is processed using an API that verifies the presence of exactly one face. After successful account creation, a unique QR code is generated for the user. This QR code allows access to secure facilities only after the system administrator has granted access privileges to the user. When a user tries to enter the secure facility, they must scan their QR code. The system then knows which face to look for and compares the live image to the one in the database to verify its identity, above certain match percentages the user's entry is approved. Additional security measures include a touch sensor that disables the entry mechanism and activates an alarm if it senses contact. Surveillance cameras installed on the roof of the facility are also used to monitor and track moving objects in the environment.


## Comprehensive Technology Overview
1. User Registration and Face Verification
Server-Side Architecture:

  FastAPI: Utilized as the primary web framework, FastAPI offers an asynchronous runtime, supporting concurrent user interactions and high-speed data processing, critical for the real-time aspects of user registration and authentication processes.
  Pydantic: This library ensures robust data validation and settings management, crucial for maintaining data integrity and security standards during user interactions.
  Firebase Admin SDK: Provides a scalable and secure backend infrastructure, facilitating user authentication and real-time data storage, which are essential for storing and managing user profiles and access logs.
  OpenCV: Deployed for sophisticated image processing tasks, OpenCV aids in the precise detection and verification of user faces during both registration and entry phases, enhancing the reliability of biometric data processing.
  face_recognition: Known for its accuracy in facial recognition tasks, this library compares live captures with registered profiles to authenticate identities with high precision.

2. Entrance System: Face Matching and QR Scanning
Technological Integration:

  OpenCV and face_recognition: These are pivotal in processing real-time video for face detection and QR code recognition, ensuring that only authorized users gain access based on facial recognition algorithms and QR code validation.
  pyzbar: Integrates QR decoding functionality directly into the system, allowing for the efficient extraction and verification of QR code data embedded within user access credentials.
  Firebase Realtime Database: Acts as a central repository for storing and querying user-specific data such as access permissions and activity logs, facilitating swift authentication and authorization decisions.
  Websocket and Requests: These technologies establish a dependable communication channel between the ESP-CAM and the server, enabling real-time data transmission and control command exchanges crucial for access management.

3. ESP-CAM and ESP32 Integration
Hardware and Firmware Capabilities:
  
  ESP-CAM: Runs a dedicated Websocket server for continuous video streaming and features built-in LED controls for signaling system states or alerts, enhancing the interactive aspect of the security apparatus.
  ESP32: Manages access control operations, integrating sensors and actuators to respond dynamically to system commands and detected threats. The inclusion of a touch sensor adds an additional layer of security by detecting unauthorized physical interactions and triggering corresponding security protocols.
  Server Communication:
  
  HTTP Server on ESP32: Facilitates robust command and control capabilities between the access management system and the ESP32, ensuring synchronized operations across the security network.
  
4. Object Tracking and Detection
Advanced Detection Technologies:
![Objection Detection](https://github.com/MrNadav/GenGuard/assets/72983086/1a56137c-2b4f-4cc1-aa6b-3ccb59629f6e)

  OpenCV: Utilized for its advanced capabilities in video processing and object detection, enabling the system to identify and track unauthorized movements or anomalies within secured areas.
  Flask: Provides a lightweight and efficient framework for deploying web applications that facilitate real-time video streaming and interaction with the object tracking system.
  Serial Communication: Essential for real-time communication between the tracking system and mechanical control systems, enabling automated responses such as camera adjustments and alert triggers based on detected movements.
  System Architecture and Integration
  Seamless Operational Flow:
  
  The GenGuard system is designed as a cohesive unit with multiple interlinked components. Each component is meticulously engineered to function both independently and as part of the integrated whole, ensuring that security operations are maintained without interruption and with maximal efficiency.
  From the initial user registration and face verification to the sophisticated entrance control mechanisms and advanced object tracking features, GenGuard leverages a comprehensive suite of technologies and frameworks to deliver a multi-layered authentication and security solution.
  The integration of client-side and server-side elements with cutting-edge hardware solutions ensures that GenGuard not only meets but exceeds the stringent requirements of modern organizational security demands, providing a scalable, reliable, and user-friendly system that stands at the forefront of access control technology.


# Installation and use

1. download the required libraries
2. build the electric circuit that showen in the picture
 ![circuit](https://github.com/MrNadav/GenGuard/assets/72983086/6fc751e2-f42c-414b-895f-fc70b389df20)
![ESP32](https://github.com/MrNadav/GenGuard/assets/72983086/9d7d0fd6-a77d-42da-9919-4497bfc9109e)

3. upload and right the codes on EPS32 and 2 esp cameras.
4. for the server side of the face match system run 'python face_system.py' in GenGuardServer\Face Match System\face_system.py
5. run the object dedection system 'final.py' in ObjetTrackingDetection\final.py
