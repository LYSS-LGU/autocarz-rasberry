# /home/pi/autocarz/src/detection/yolo_detector.py
# YOLO v8 기반 객체 인식 담당

from ultralytics import YOLO

class YoloDetector:
    def __init__(self, model_path):
        """
        YOLO 모델을 불러와 초기화합니다.
        model_path: 학습된 모델 파일 경로 (예: models/best.pt)
        """
        try:
            self.model = YOLO(model_path)
            print("[YOLO] 모델 로드 성공!")
        except Exception as e:
            print(f"[YOLO] 모델 로드 실패: {e}")
            self.model = None

    def detect(self, frame):
        """
        입력 프레임에서 객체를 탐지하고 결과를 반환합니다.
        frame: numpy 배열 (BGR 또는 RGB)
        return: YOLO 탐지 결과 객체 또는 None
        """
        if self.model:
            return self.model(frame, verbose=False)
        return None 