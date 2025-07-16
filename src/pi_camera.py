# /home/pi/autocarz/src/pi_camera.py

import cv2
from ultralytics import YOLO

# 1. 모델 로드
try:
    model = YOLO('/home/pi/autocarz/models/best.pt')  # ✅ 정확한 상대경로로 수정
    print("✅ 모델 로드 성공!")
except Exception as e:
    print(f"❌ 모델 로드 실패: {e}")
    exit()

# 2. 카메라 초기화
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ 카메라를 열 수 없습니다. 연결 상태를 확인하세요.")
    cap.release()
    exit()

print("✅ 실시간 탐지를 시작합니다. 종료하려면 'q' 키를 누르세요.")

# 3. 메인 루프
while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ 프레임을 읽어오는 데 실패했습니다.")
        break
    
    results = model(frame, verbose=False)
    annotated_frame = results[0].plot()
    cv2.imshow("Realtime Detection on Pi", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 4. 정리
print("✅ 시스템을 종료합니다.")
cap.release()
cv2.destroyAllWindows()
