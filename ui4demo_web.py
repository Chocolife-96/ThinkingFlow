import cv2
import base64
import threading
import time
from flask import Flask, render_template_string
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

camera = cv2.VideoCapture(0)
frame_lock = threading.Lock()
latest_frame = None

def camera_loop():
    global latest_frame
    while True:
        success, frame = camera.read()
        if success:
            with frame_lock:
                latest_frame = frame.copy()
        time.sleep(1 / 15)

def emit_frames():
    while True:
        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()
        _, buffer = cv2.imencode('.jpg', frame)
        encoded = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('video_frame', encoded)
        time.sleep(1 / 15)

HTML_PAGE = '''
<!DOCTYPE html>
<html>
<body>
    <h2>WebSocket Video</h2>
    <img id="video" style="width:80%;">
    <script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
    <script>
        const socket = io();
        socket.on('video_frame', data => {
            document.getElementById('video').src = 'data:image/jpeg;base64,' + data;
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    threading.Thread(target=camera_loop, daemon=True).start()
    threading.Thread(target=emit_frames, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
