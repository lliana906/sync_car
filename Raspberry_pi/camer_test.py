import cv2
from flask import Flask, Response

app = Flask(__name__)
cap = cv2.VideoCapture(0) # 안 되면 1이나 2로 변경

def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # 프레임을 웹 브라우저가 인식할 수 있는 JPEG 포맷으로 인코딩
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # 스트리밍 데이터 포맷으로 쪼개서 전송
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    # 웹 브라우저가 접속하면 실시간 이미지 스트리밍 실행
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("🚀 웹 스트리밍 서버 가동 중...")
    # 라즈베리파이 IP 주소에 상관없이 5000번 포트로 개방
    app.run(host='0.0.0.0', port=5000, debug=False)