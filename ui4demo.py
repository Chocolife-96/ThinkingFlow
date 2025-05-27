from flask import Flask, render_template_string, Response, request
import cv2
import threading
import time

app = Flask(__name__)
camera = cv2.VideoCapture(0)

frame_lock = threading.Lock()
latest_frame = None

# 要轮播的文字
word_list = ["morning", "nihao", "bye"]
current_word = "hello"

# 控制标志：不同路径返回不同的流
STREAM_TOP = "/video_feed_top"
STREAM_PLAIN = "/video_feed_plain"

# 摄像头采集线程
def capture_camera():
    global latest_frame
    while True:
        success, frame = camera.read()
        if not success:
            break
        with frame_lock:
            latest_frame = frame.copy()

# 文字切换线程
def rotate_text():
    global current_word
    i = 0
    while True:
        current_word = word_list[i % len(word_list)]
        i += 1
        time.sleep(2)

# 启动线程
threading.Thread(target=capture_camera, daemon=True).start()
threading.Thread(target=rotate_text, daemon=True).start()

# 视频流生成器
def gen_frames(with_text=False):
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        if with_text:
            height, width, _ = frame.shape
            cv2.putText(frame, current_word, (width - 150, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 255, 0), 2, cv2.LINE_AA)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# HTML 页面
HTML_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>三窗口摄像头轮播文字</title>
    <style>
        body { margin: 0; background: #111; }
        .container {
            display: grid;
            grid-template-rows: 1fr 1fr;
            grid-template-columns: 1fr 1fr;
            height: 100vh;
            gap: 2px;
        }
        .top {
            grid-column: 1 / 3;
        }
        .view {
            background: black;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        img {
            max-width: 100%;
            max-height: 100%;
            border: 2px solid #ccc;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="view top"><img src="{{ url_for('video_feed_top') }}"></div>
        <div class="view"><img src="{{ url_for('video_feed_plain') }}"></div>
        <div class="view"><img src="{{ url_for('video_feed_plain') }}"></div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/video_feed_top')
def video_feed_top():
    return Response(gen_frames(with_text=True),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_plain')
def video_feed_plain():
    return Response(gen_frames(with_text=False),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
