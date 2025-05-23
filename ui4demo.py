from flask import Flask, render_template_string, Response
import cv2

app = Flask(__name__)
camera = cv2.VideoCapture(0)

HTML_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>摄像头实时画面</title>
</head>
<body>
    <h2>摄像头实时画面（右上角写有 hello）</h2>
    <img src="{{ url_for('video_feed') }}" width="640" height="480">
</body>
</html>
'''

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        # 添加文字“hello”到右上角
        height, width, _ = frame.shape
        cv2.putText(frame, "hello", (width - 100, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)

        # 编码为 JPEG 格式
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # 用 multipart 流方式发送
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)