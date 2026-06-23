import cv2
import numpy as np
from flask import Flask, Response

app = Flask(__name__)
cap = cv2.VideoCapture(0)

# 웹캠 해상도 설정
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        # ---------------------------------------------------------
        # [1단계] ROI 구역 정하기 (관심 영역 설정)
        # ---------------------------------------------------------
        # 화면 전체(640x480)를 다 보면 연산이 느리고 엉뚱한 노이즈가 잡힙니다.
        # 화면 중앙 부근에 가로 200, 세로 150 크기의 사각형 구역을 지정합니다.
        x_start, y_start, width, height = 220, 160, 200, 150
        roi = frame[y_start:y_start+height, x_start:x_start+width]
        
        # ---------------------------------------------------------
        # [2단계] 색상 인식을 위해 BGR을 HSV 색 공간으로 변환
        # ---------------------------------------------------------
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # HSV 색상 범위 정의 (라즈베리파이 카메라 특성에 맞게 조정 필요)
        # 초록색 범위
        lower_green = np.array([35, 50, 50])
        upper_green = np.array([85, 255, 255])
        
        # 노란색 범위
        lower_yellow = np.array([15, 50, 50])
        upper_yellow = np.array([35, 255, 255])
        
        # 빨간색 범위 (빨간색은 HSV 구조상 0 부근과 180 부근 두 영역으로 나뉩니다)
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([165, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        
        # ---------------------------------------------------------
        # [3단계] 마스크 생성 및 색상 픽셀 개수 세기
        # ---------------------------------------------------------
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        # 각 마스크 내에서 감지된 흰색(색상에 해당하는) 픽셀의 개수 카운트
        cnt_red = cv2.countNonZero(mask_red)
        cnt_yellow = cv2.countNonZero(mask_yellow)
        cnt_green = cv2.countNonZero(mask_green)
        
        # ---------------------------------------------------------
        # [4단계] 기준값(Threshold) 비교 후 결과 값 출력
        # ---------------------------------------------------------
        color_result = -1 # 아무것도 검출되지 않음
        color_name = "None"
        
        # 구역 내에 특정 색상 픽셀이 500개 이상 모여있을 때만 인식한 것으로 인정 (노이즈 방지)
        threshold = 500 
        
        # 가장 픽셀이 많이 뭉쳐있는 색상을 우선 선택
        max_cnt = max(cnt_red, cnt_yellow, cnt_green)
        
        if max_cnt > threshold:
            if max_cnt == cnt_red:
                color_result = 0
                color_name = "RED (0)"
            elif max_cnt == cnt_yellow:
                color_result = 1
                color_name = "YELLOW (1)"
            elif max_cnt == cnt_green:
                color_result = 2
                color_name = "GREEN (2)"
                
        # VS Code 터미널 창에 결과 프린트!
        if color_result != -1:
            print(f"🚦 감지된 색상: {color_name} (값: {color_result})")
            
        # ---------------------------------------------------------
        # [5단계] 브라우저 화면에 시각적으로 구역 그려주기
        # ---------------------------------------------------------
        # 원본 화면에 ROI 구역을 초록색 사각형(두께 2)으로 그려서 모니터링하기 쉽게 만듭니다.
        cv2.rectangle(frame, (x_start, y_start), (x_start+width, y_start+height), (0, 255, 0), 2)
        
        # 인식된 색상 이름을 화면 좌상단에 텍스트로도 띄워줍니다.
        if color_result != -1:
            cv2.putText(frame, f"Detect: {color_name}", (x_start, y_start - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # JPEG 인코딩 및 스트리밍 전송
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("🚀 실시간 색상 인식 웹 서버 가동 중... 노트북 브라우저를 확인하세요!")
    app.run(host='0.0.0.0', port=5000, debug=False)