# /home/pi/autocarz/src/main.py
import cv2
import configparser
from yolo_detector import YoloDetector
from yolo_visualizer import YoloVisualizer
# import time # 나중에 자동 저장 시 사용

def main():
    # --- 설정 불러오기 ---
    config = configparser.ConfigParser()
    config.read('../config.ini') # 상위 폴더의 config.ini 파일 읽기

    model_path = config['YOLO']['MODEL_PATH']
    conf_threshold = float(config['YOLO']['CONFIDENCE_THRESHOLD'])
    cam_index = int(config['CAMERA']['INDEX'])
    font_path = config['FONT']['PATH']
    font_size_large = int(config['FONT']['SIZE_LARGE'])
    font_size_small = int(config['FONT']['SIZE_SMALL'])

    # --- 전문가 객체 생성 ---
    detector = YoloDetector(model_path)
    visualizer = YoloVisualizer(font_path, font_size_large, font_size_small)
    
    # --- 카메라 실행 ---
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print(f"❌ 카메라 {cam_index}번을 열 수 없습니다.")
        return

    print("✅ 시스템 시작! (종료: q)")

    # --- 메인 루프 ---
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # 1. 탐지 전문가에게 일을 시킴
        results = detector.detect(frame)

        # 2. 시각화 전문가에게 일을 시킴
        annotated_frame, detected = visualizer.draw_detections(frame, results, conf_threshold)

        # 3. 최종 결과 화면에 표시
        cv2.imshow("AUTOCARZ Detection System", annotated_frame)
        
        # 4. 탐지 시 행동 (나중에 여기에 아두이노/서버 연동 코드 추가)
        if detected:
            print("🚨 고라니 탐지!")
            # time.sleep(1) # 연속 탐지 방지

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    print("✅ 시스템 종료.")

if __name__ == "__main__":
    main()