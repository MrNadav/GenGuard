import cv2
import websocket
import numpy as np
import threading

def on_message(ws, message):
    # Convert the binary frame to a numpy array
    nparr = np.frombuffer(message, np.uint8)
    # Decode the numpy array to an OpenCV image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Display the image
    cv2.imshow('ESP32-CAM Stream', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        ws.close()

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")
    cv2.destroyAllWindows()

def on_open(ws):
    print("Opened connection")

# WebSocket address
ws_address = 'ws://192.168.229.182:81'

# Create a WebSocket app
ws = websocket.WebSocketApp(ws_address,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

# Run the WebSocket in a separate thread
wst = threading.Thread(target=ws.run_forever)
wst.daemon = True
wst.start()

# Keep the main thread alive
try:
    while True:
        pass
except KeyboardInterrupt:
    ws.close()
