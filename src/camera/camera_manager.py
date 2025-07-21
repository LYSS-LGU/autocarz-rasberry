# /home/pi/autocarz/src/camera/camera_manager.py
# YOLO,openCV 색상 및 크기 구분 기능 추가

import cv2
import time
import platform
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

        # === [차이점 1] 모든 설정을 __init__에서 중앙 관리합니다 ===
        # 이렇게 하면 코드가 더 깔끔해지고, 나중에 설정을 바꿀 때 이 부분만 수정하면 됩니다.
        
        # 1. 객체 탐지 모델 활성화 설정
        self.yolo_enabled = True
        self.opencv_enabled = True
        print("   -> 💡 YOLO와 OpenCV 동시 탐지 모드가 활성화되었습니다.")
        
        # 2. 플랫폼별 자동 최적화 설정
        # 64비트 라즈베리파이(aarch64)도 정확하게 감지하도록 로직을 개선했습니다.
        machine_type = platform.machine().lower()
        self.is_raspberry_pi = 'arm' in machine_type or 'aarch64' in machine_type

        if self.is_raspberry_pi:
            # 🍓 라즈베리파이 환경: 성능 최적화 모드
            self.target_width, self.target_height, self.target_fps = 640, 480, 15
            self.detection_interval = 3  # 3프레임마다 한 번씩만 탐지하여 CPU 부하를 줄입니다.
            print(f"   -> 🍓 라즈베리파이 환경 감지! 성능 최적화 모드로 설정합니다.")
        else:
            # 💻 노트북/데스크탑 환경: 고품질 모드
            self.target_width, self.target_height, self.target_fps = 1280, 720, 30
            self.detection_interval = 1  # 매 프레임마다 탐지하여 실시간 정확도를 높입니다.
            print(f"   -> 💻 노트북/PC 환경 감지! 고품질 모드로 설정합니다.")
            
        print(f"   -> 📊 최종 설정: {self.target_width}x{self.target_height} @ {self.target_fps}fps, 검출간격: {self.detection_interval}프레임")
        
        # 3. 프레임 카운터 초기화 (검출 빈도 제어용)
        self.frame_count = 0
        
        # 4. 검출 결과 저장 및 유지 시간 설정
        self.detection_results = {
            'yolo': {'boxes': [], 'timestamp': 0},
            'opencv': {'boxes': [], 'timestamp': 0}
        }
        self.result_keep_time = 5.0  # 검출 결과를 5초간 유지

    def start_camera(self, index=0):
        with self.lock:
            print(f"📷 카메라 (인덱스 {index}) 시작을 시도합니다...")
            
            if self.cap is not None:
                self.is_running = False
                self.cap.release()
                self.cap = None
                time.sleep(1)

            self.camera_index = index
            
            if platform.system().lower() == "windows":
                # Windows에서는 DirectShow 사용
                self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            else:
                # Linux/라즈베리파이에서는 기본 백엔드 사용
                self.cap = cv2.VideoCapture(index)
            
            if not self.cap or not self.cap.isOpened():
                print(f"❌ 에러: 카메라 {index}를 열 수 없습니다.")
                self.is_running = False
                return False
            
            # === [차이점 2] __init__에서 미리 정해둔 설정값을 가져와 사용합니다 ===
            # start_camera 함수는 이제 카메라를 '켜는' 역할에만 집중합니다.
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            print(f"   -> 카메라에 설정 적용 완료.")
            
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

    def put_text_safe(self, img, text, position, font_scale=0.5, color=(255, 255, 255), thickness=1):
        try:
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            # 텍스트 크기 계산
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            bg_rect_pt1 = (position[0], position[1] - text_height - baseline)
            bg_rect_pt2 = (position[0] + text_width, position[1] + baseline)
            cv2.rectangle(img, bg_rect_pt1, bg_rect_pt2, (0,0,0), -1) # 검은색 배경
            cv2.putText(img, text, position, font, font_scale, color, thickness, cv2.LINE_AA)
        except Exception as e:
            print(f"텍스트 렌더링 오류: {e}")

    def generate_frames(self):
        # === [차이점 3] __init__에서 미리 정해둔 FPS 값을 가져와 사용합니다 ===
        frame_time = 1.0 / self.target_fps
        last_frame_time = time.time()
        
        while True:
            current_time = time.time()
            
            # FPS 제한 적용
            if current_time - last_frame_time < frame_time:
                time.sleep(0.005) # CPU 사용량을 줄이기 위해 짧게 대기
                continue
            
            last_frame_time = current_time

            frame = None
            with self.lock:
                if not self.is_running or self.cap is None:
                    time.sleep(0.1)
                    continue
                ret, frame = self.cap.read()

            if frame is None: continue

            try:
                # === [석이님 아이디어] 프레임별 검출 빈도 제어 ===
                self.frame_count += 1
                should_detect = (self.frame_count % self.detection_interval == 0)
                current_time = time.time()
                
                # 디버그: 5초마다 검출 상태 출력
                if hasattr(self, '_last_debug_time'):
                    if current_time - self._last_debug_time > 5:
                        yolo_count = len(self.detection_results['yolo']['boxes'])
                        opencv_count = len(self.detection_results['opencv']['boxes'])
                        print(f"🔍 검출 상태 - YOLO: {yolo_count}개, OpenCV: {opencv_count}개")
                        self._last_debug_time = current_time
                else:
                    self._last_debug_time = current_time
                
                # 새로운 검출 수행 (3프레임마다)
                if should_detect:
                    # 1. YOLO 탐지 (파란색)
                    if self.yolo_enabled and self.yolo.model:
                        results = self.yolo.detect(frame)
                        if results:
                            yolo_boxes = []
                            for r in results:
                                for box in r.boxes:
                                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                                    conf = float(box.conf[0])
                                    cls_id = int(box.cls[0])
                                    class_name = self.yolo.model.names.get(cls_id, f"Class_{cls_id}")
                                    # 한글 클래스명 처리
                                    if isinstance(class_name, str) and not class_name.isascii():
                                        class_name = f"Class_{cls_id}"
                                    
                                    # 디버그: 클래스 ID와 이름 출력
                                    print(f"🦌 YOLO 검출 - ID: {cls_id}, 이름: {class_name}, 신뢰도: {conf:.2f}")
                                    
                                    yolo_boxes.append({
                                        'coords': (x1, y1, x2, y2),
                                        'conf': conf,
                                        'class_name': class_name
                                    })
                            # 검출 결과 저장
                            self.detection_results['yolo'] = {
                                'boxes': yolo_boxes,
                                'timestamp': current_time
                            }

                    # 2. OpenCV 탐지 (빨간색)
                    if self.opencv_enabled and self.opencv.yolo_model:
                        opencv_results = self.opencv.detect_yolo_objects(frame)
                        if opencv_results:
                            opencv_boxes = []
                            for r in opencv_results:
                                for box in r.boxes:
                                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                                    conf = float(box.conf[0])
                                    cls_id = int(box.cls[0])
                                    class_name = self.opencv.yolo_model.names.get(cls_id, f"Class_{cls_id}")
                                    # 한글 클래스명 처리
                                    if isinstance(class_name, str) and not class_name.isascii():
                                        class_name = f"Class_{cls_id}"
                                    
                                    # 디버그: 클래스 ID와 이름 출력
                                    print(f"🔴 OpenCV 검출 - ID: {cls_id}, 이름: {class_name}, 신뢰도: {conf:.2f}")
                                    
                                    opencv_boxes.append({
                                        'coords': (x1, y1, x2, y2),
                                        'conf': conf,
                                        'class_name': class_name
                                    })
                            # 검출 결과 저장
                            self.detection_results['opencv'] = {
                                'boxes': opencv_boxes,
                                'timestamp': current_time
                            }
                
                # === 검출 결과 그리기 (5초간 유지) ===
                # YOLO 결과 그리기
                yolo_time_diff = current_time - self.detection_results['yolo']['timestamp']
                if yolo_time_diff < self.result_keep_time:
                    for box_info in self.detection_results['yolo']['boxes']:
                        x1, y1, x2, y2 = box_info['coords']
                        color = (255, 191, 0)  # 파란색 (BGR)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        label = f'YOLO: {box_info["class_name"]} {box_info["conf"]:.2f}'
                        self.put_text_safe(frame, label, (x1, y1 - 10), color=color)
                
                # OpenCV 결과 그리기
                opencv_time_diff = current_time - self.detection_results['opencv']['timestamp']
                if opencv_time_diff < self.result_keep_time:
                    for box_info in self.detection_results['opencv']['boxes']:
                        x1, y1, x2, y2 = box_info['coords']
                        color = (0, 0, 255)  # 빨간색 (BGR)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        label = f'OpenCV: {box_info["class_name"]} {box_info["conf"]:.2f}'
                        self.put_text_safe(frame, label, (x1, y2 + 20), color=color)

            except Exception as e:
                print(f"탐지/그리기 중 오류 발생: {e}")

            (flag, encodedImage) = cv2.imencode(".jpg", frame)
            if not flag: continue
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                  bytearray(encodedImage) + b'\r\n')

# 전역 카메라 매니저 인스턴스
camera_manager = CameraManager()