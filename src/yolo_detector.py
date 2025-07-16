# /home/pi/autocarz/src/yolo_detector.py
from ultralytics import YOLO

class YoloDetector:
    def __init__(self, model_path):
        """모델 경로를 받아 초기화합니다."""
        try:
            self.model = YOLO(model_path)
            print("✅ YOLO Detector: 모델 로드 성공!")
        except Exception as e:
            print(f"❌ YOLO Detector: 모델 로드 실패: {e}")
            self.model = None

    def detect(self, frame):
        """입력된 프레임에서 객체를 탐지하고 결과를 반환합니다."""
        if self.model:
            return self.model(frame, verbose=False)
        return None