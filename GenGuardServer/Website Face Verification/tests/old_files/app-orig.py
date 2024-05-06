#server
from flask import Flask, request, jsonify
from flask_cors import CORS
#face rec
import cv2
import numpy as np
#firebase
import firebase_admin
from firebase_admin import credentials, auth, db, storage
import datetime

#qr
import qrcode
from io import BytesIO

#barcode test
from barcode import Code128
from barcode.writer import ImageWriter

#barcode resize
from PIL import Image

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("fb/fb.json")
firebase_admin.initialize_app(cred, {'storageBucket': '', 'databaseURL': ''})

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@app.route('/verify-face', methods=['POST'])
def verify_face():
    if 'file' not in request.files:
        return jsonify(success=False, error='No file part'), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, error='No selected file'), 400
    
    filestr = file.read()
    npimg = np.frombuffer(filestr, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify(success=False, error='Error reading image'), 400

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces) == 0:
        return jsonify(success=False, error='No face detected'), 400
    elif len(faces) > 1:
        return jsonify(success=False, error='Multiple faces detected'), 400
    
    return jsonify(success=True)

@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify(success=False, error='User ID is required'), 400
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4,)
    qr.add_data(user_id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    img_bytes = BytesIO()
    img.save(img_bytes)
    img_bytes.seek(0)

    # Upload QR code to Firebase Storage
    blob = storage.bucket().blob(f'qrcodes/{user_id}.png')
    blob.upload_from_string(img_bytes.getvalue(), content_type='image/png')
    qr_url = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')

    # Save user ID and QR code URL to Firebase Realtime Database or Firestore
    ref = db.reference('users')
    user_ref = ref.child(user_id)
    user_ref.set({'qr_url': qr_url})

    return jsonify(success=True, qr_url=qr_url)




from firebase_admin import storage

@app.route('/deleteUser', methods=['DELETE'])
def delete_user():
    user_id = request.json.get('uid')
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

        return jsonify({'message': 'User and files deleted successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
        app.run(debug=True, port=5569, host='0.0.0.0')










#TEST ON WEB face rec
# // URL of the image file on your server
# const imageUrl = 'http://127.0.0.1:5500/static/img/person.jpg';

# fetch(imageUrl).then(response => response.blob()).then(blob => {
#     const formData = new FormData();
    
#     formData.append('file', blob, 'your_image_file.extension'); 
    
#     fetch('http://127.0.0.1:5000/verify-face', { method: 'POST', body: formData })
#         .then(response => response.json())
#         .then(data => console.log('Response from server:', data))
#         .catch(error => console.error('Error during fetch:', error));
# });