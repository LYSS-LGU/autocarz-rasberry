# /home/pi/autocarz/src/camera/camera_manager.py
# YOLO,openCV 색상 및 크기 구분 기능 추가

import cv2
import time
import numpy as np
from threading import Lock
from detection.yolo_detector import YoloDetector
from detection.opencv_detector import OpenCVCascadeDetector

class CameraManager:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.lock = Lock()
        self.camera_index = -1

        print("🤖 객체 탐지 모델들을 로딩합니다...")
        self.yolo = YoloDetector(model_path='models/best.pt') 
        # OpenCV도 같은 YOLO 모델을 사용
        self.opencv = OpenCVCascadeDetector(cascade_dir='models/haarcascades', yolo_model_path='models/best.pt')
        print("✅ 모든 모델 로딩 완료!")

        # YOLO 모델 클래스 정보 출력
        if self.yolo.model:
            print(f"📋 YOLO 모델 클래스 목록:")
            for i, name in self.yolo.model.names.items():
                print(f"   Class_{i}: {name}")
            
            # 만약 클래스 이름이 숫자로만 되어 있다면, 사용자가 직접 설정할 수 있음
            if len(self.yolo.model.names) > 0:
                first_class = list(self.yolo.model.names.values())[0]
                if first_class.isdigit() or first_class.startswith('Class_'):
                    print("⚠️ 클래스 이름이 숫자로 되어 있습니다. data.yaml 파일이 필요할 수 있습니다.")
                    print("💡 훈련 폴더에서 data.yaml 파일을 models/ 폴더로 복사해주세요.")
        else:
            print("⚠️ YOLO 모델이 로드되지 않았습니다.")

        self.yolo_enabled = True
        self.opencv_enabled = True

    def start_camera(self, index=0):
        with self.lock:
            print(f"📷 카메라 (인덱스 {index}) 시작을 시도합니다...")
            self.camera_index = index
            self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            
            if not self.cap or not self.cap.isOpened():
                print(f"❌ 에러: 카메라 {index}를 열 수 없습니다.")
                self.is_running = False
                return False
            
            self.is_running = True
            print(f"✅ 카메라 {index}가 성공적으로 시작되었습니다.")
            return True

    def stop_camera(self):
        with self.lock:
            if self.cap:
                self.is_running = False
                self.cap.release()
                self.cap = None
                print("🔌 카메라가 정지되었습니다.")

    def put_text_safe(self, img, text, position, font_scale=0.6, color=(255, 255, 255), thickness=2):
        """
        안전한 텍스트 렌더링 함수 - 폰트 문제 방지
        """
        try:
            # 기본 폰트 사용
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            # 텍스트 크기 계산
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            
            # 텍스트 그리기
            cv2.putText(img, text, position, font, font_scale, color, thickness)
            
            return text_width, text_height
        except Exception as e:
            print(f"텍스트 렌더링 오류: {e}")
            return 0, 0

    def generate_frames(self):
        while True:
            with self.lock:
                if not self.is_running or self.cap is None:
                    time.sleep(0.1)
                    continue
                ret, frame = self.cap.read()

            if not ret or frame is None:
                continue

            try:
                # 1. YOLO 탐지 및 결과 그리기 (파란색 박스)
                if self.yolo_enabled and self.yolo.model:
                    results = self.yolo.detect(frame)
                    if results is not None:
                        for r in results:
                            for box in r.boxes:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                
                                # YOLO는 파란색으로 그립니다 (BGR: 255, 0, 0)
                                color_yolo = (255, 0, 0)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), color_yolo, 2)
                                
                                # 신뢰도와 클래스 정보 (영어로 표시)
                                conf = round(float(box.conf[0]), 2)
                                cls_id = int(box.cls[0])
                                
                                # 클래스 이름을 영어로 변환
                                class_name = f"Class_{cls_id}"  # 기본값
                                if (self.yolo and self.yolo.model and 
                                    hasattr(self.yolo.model, 'names') and 
                                    self.yolo.model.names and 
                                    cls_id in self.yolo.model.names):
                                    class_name = self.yolo.model.names[cls_id]
                                    if isinstance(class_name, str):
                                        # 한글이나 특수문자가 있으면 영어로 대체
                                        if not class_name.isascii():
                                            class_name = f"Class_{cls_id}"
                                    else:
                                        class_name = f"Class_{cls_id}"
                                
                                label = f'YOLO: {class_name} ({conf})'
                                
                                # 라벨 배경과 텍스트 그리기 (안전한 함수 사용)
                                text_width, text_height = self.put_text_safe(frame, label, (x1, y1 - 5), 0.5, (255, 255, 255), 1)
                                if text_width > 0:
                                    cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width, y1), color_yolo, -1)
                                    self.put_text_safe(frame, label, (x1, y1 - 5), 0.5, (255, 255, 255), 1)

                # 2. OpenCV YOLO 탐지 및 결과 그리기 (빨간색 박스, 더 큰 크기)
                if self.opencv_enabled:
                    # OpenCV도 YOLO 모델을 사용해서 같은 객체 탐지
                    opencv_results = self.opencv.detect_yolo_objects(frame)
                    
                    # OpenCV 탐지 디버그 정보 (5초마다 출력)
                    if hasattr(self, '_last_debug_time'):
                        if time.time() - self._last_debug_time > 5:
                            if opencv_results:
                                detection_count = sum(len(r.boxes) for r in opencv_results)
                                print(f"🔍 OpenCV YOLO 탐지: {detection_count}개 발견")
                            else:
                                print(f"🔍 OpenCV YOLO 탐지: 0개 발견")
                            self._last_debug_time = time.time()
                    else:
                        self._last_debug_time = time.time()
                        if opencv_results:
                            detection_count = sum(len(r.boxes) for r in opencv_results)
                            print(f"🔍 OpenCV YOLO 탐지 시작: {detection_count}개 발견")
                        else:
                            print(f"🔍 OpenCV YOLO 탐지 시작: 0개 발견")
                    
                    if opencv_results:
                        for r in opencv_results:
                            for box in r.boxes:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                
                                # YOLO보다 크게 보이도록 패딩을 줍니다 (겹침 방지)
                                padding = 15
                                x1 = max(0, x1 - padding)
                                y1 = max(0, y1 - padding)
                                x2 = min(frame.shape[1], x2 + padding)
                                y2 = min(frame.shape[0], y2 + padding)

                                # OpenCV는 빨간색으로 그립니다 (BGR: 0, 0, 255)
                                color_opencv = (0, 0, 255)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), color_opencv, 3)
                                
                                # 신뢰도와 클래스 정보
                                conf = round(float(box.conf[0]), 2)
                                cls_id = int(box.cls[0])
                                
                                # 클래스 이름을 영어로 변환
                                # 오류 원인: self.yolo.model이 None이거나, model에 names 속성이 없어서 발생합니다.
                                # OpenCV 탐지에서는 self.yolo가 아니라 self.opencv.yolo_model을 사용해야 합니다.
                                # 아래와 같이 수정해야 오류가 발생하지 않습니다.
                                class_name = f"Class_{cls_id}"  # 기본값
                                if (self.opencv and self.opencv.yolo_model and 
                                    hasattr(self.opencv.yolo_model, "names") and 
                                    self.opencv.yolo_model.names and 
                                    cls_id in self.opencv.yolo_model.names):
                                    class_name = self.opencv.yolo_model.names[cls_id]
                                
                                if isinstance(class_name, str):
                                    # 한글이나 특수문자가 있으면 영어로 대체
                                    if not class_name.isascii():
                                        class_name = f"Class_{cls_id}"
                                else:
                                    class_name = f"Class_{cls_id}"
                                
                                label = f'OpenCV: {class_name} ({conf})'
                                
                                # 라벨 그리기 (안전한 함수 사용)
                                text_width, text_height = self.put_text_safe(frame, label, (x1, y1 - 5), 0.5, (255, 255, 255), 1)
                                if text_width > 0:
                                    cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width, y1), color_opencv, -1)
                                    self.put_text_safe(frame, label, (x1, y1 - 5), 0.5, (255, 255, 255), 1)

            except Exception as e:
                print(f"탐지 중 오류 발생: {e}")

            # 3. JPEG로 인코딩하여 스트리밍
            (flag, encodedImage) = cv2.imencode(".jpg", frame)
            if not flag:
                continue
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                  bytearray(encodedImage) + b'\r\n')

# 전역 카메라 매니저 인스턴스
camera_manager = CameraManager()