from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import qrcode
from io import BytesIO
import asyncio
from firebase_admin import credentials, storage, initialize_app
import datetime
import uvicorn
import traceback
from pydantic import BaseModel
#face rec
import cv2
import numpy as np
from mtcnn.mtcnn import MTCNN
import face_recognition
#firebase
import firebase_admin
from firebase_admin import credentials, auth, db, storage
import datetime
#qr
import qrcode
from io import BytesIO
import logging
import time  # Import the time module


app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("fb/fb.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': '',
    'databaseURL': ''  # Replace with your actual Firebase database URL
})


def upload_qr_to_firebase(img_bytes, user_id):
    """
    Uploads QR code to Firebase Storage and returns the URL.
    This is a synchronous function.
    """
    bucket = storage.bucket()

    blob = bucket.blob(f'qrcodes/{user_id}.png')
    blob.upload_from_string(img_bytes.getvalue(), content_type='image/png')

    # Generate signed URL for the QR code image
    qr_url = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')
    return qr_url

@app.post('/api/generate-qr')
async def generate_qr(request: Request):
    data = await request.json()
    user_id = data.get('user_id')
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    # Generate QR code
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(user_id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    img_bytes = BytesIO()
    img.save(img_bytes)
    img_bytes.seek(0)

    # Upload QR code to Firebase Storage
    qr_url = await asyncio.get_event_loop().run_in_executor(None, upload_qr_to_firebase, img_bytes, user_id)

    return {"success": True, "qr_url": qr_url}


# @app.post('/api/verify-face')
# async def verify_face(file: UploadFile = File(...)):
#     start_time = time.time()
#     content = await file.read()
#     npimg = np.frombuffer(content, np.uint8)
#     img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

#     if img is None:
#         raise HTTPException(status_code=400, detail="Error reading image")

#     # Convert the image from BGR color (which OpenCV uses) to RGB color
#     rgb_img = img[:, :, ::-1]
#     print("before faces locations")

#     # Start measuring time
#     start_time = time.time()
#     # Run face detection
#     face_locations = face_recognition.face_locations(rgb_img)

#     # Stop measuring time
#     end_time = time.time()


#     if len(face_locations) == 0:
#         raise HTTPException(status_code=400, detail="No face detected")
#     elif len(face_locations) > 1:
#         raise HTTPException(status_code=400, detail="Multiple faces detected")
#     end_time = time.time()
#     detection_time = end_time - start_time  # Calculate the detection time
#     print(f"Detection Time: {detection_time:.4f} seconds")

#     return {"success": True, "face_locations": face_locations, "detection_time": detection_time}



@app.post('/api/verify-face')
async def verify_face(file: UploadFile = File(...)):
    start_time = time.time()
    content = await file.read()
    npimg = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Error reading image")

    # Convert the image from BGR color (which OpenCV uses) to RGB color
    # (This step might be optional if you're just detecting faces, not recognizing them)
    rgb_img = img[:, :, ::-1]

    # Load Haar Cascade for frontal face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Detect faces in the image
    face_locations = face_cascade.detectMultiScale(rgb_img, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

    if len(face_locations) == 0:
        raise HTTPException(status_code=400, detail="No face detected")
    elif len(face_locations) > 1:
        raise HTTPException(status_code=400, detail="Multiple faces detected")

    detection_time = time.time() - start_time  # Calculate the detection time
    print(f"Detection Time: {detection_time:.4f} seconds")

    return {"success": True, "face_locations": face_locations.tolist(), "detection_time": detection_time}

class UserDeleteRequest(BaseModel):
    uid: str

@app.delete('/api/deleteUser')
async def delete_user(user_delete_request: UserDeleteRequest):  # Use Pydantic model for automatic request parsing
    user_id = user_delete_request.uid

    if not user_id:
        return JSONResponse(content={'error': "The 'uid' field is required."}, status_code=400)

    try:
        # Delete from Firebase Authentication
        auth.delete_user(user_id)

        # Delete from Firebase Realtime Database
        db.reference(f'users/{user_id}').delete()

        # Firebase Storage: Delete specific user files
        bucket = storage.bucket()
        file_paths = [
            f"qrcodes/{user_id}.png",
            f"user_photos/{user_id}.png"
        ]

        for file_path in file_paths:
            blob = bucket.blob(file_path)
            blob.delete()

        return JSONResponse(content={'message': 'User and files deleted successfully'}, status_code=status.HTTP_200_OK)

    except firebase_admin.exceptions.FirebaseError as firebase_error:
        logger.error(f"Firebase error deleting user {user_id}: {str(firebase_error)}")
        return JSONResponse(content={'error': str(firebase_error)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return JSONResponse(content={'error': 'An unexpected error occurred'}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5569, log_level="debug")