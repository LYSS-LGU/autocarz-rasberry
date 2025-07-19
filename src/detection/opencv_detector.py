# /home/pi/autocarz/src/detection/opencv_detector.py
# OpenCV 기반 객체 인식 (YOLO 모델과 함께 사용)

import cv2
import os
import numpy as np
from ultralytics import YOLO

class OpenCVCascadeDetector:
    def __init__(self, cascade_dir=None, yolo_model_path=None):
        """
        OpenCV 기반 객체 인식 초기화
        cascade_dir: Haar cascade 파일들이 있는 폴더 경로 (선택사항)
        yolo_model_path: YOLO 모델 경로 (OpenCV도 같은 모델 사용)
        """
        self.cascades = {}
        self.yolo_model = None
        
        # 1. YOLO 모델 로드 (OpenCV도 같은 모델 사용)
        if yolo_model_path and os.path.exists(yolo_model_path):
            try:
                self.yolo_model = YOLO(yolo_model_path)
                print(f"✅ OpenCV용 YOLO 모델 로드 성공: {yolo_model_path}")
            except Exception as e:
                print(f"❌ OpenCV용 YOLO 모델 로드 실패: {e}")
        
        # 2. OpenCV 내장 cascade (얼굴 탐지용)
        try:
            # 오류 원인: 일부 OpenCV 설치 환경(특히 라즈베리파이, 경량 빌드 등)에서는 cv2 모듈에 'data' 속성이 없어서
            # 'cv2.data' 또는 'cv2.data.haarcascades' 접근 시 AttributeError가 발생합니다.
            # 즉, "data" is not a known attribute of module "cv2" 에러가 뜹니다.
            # OpenCV를 pip로 설치하면 대부분 포함되어 있지만, 소스 빌드/경량 패키지 등에서는 누락될 수 있습니다.
            # 해결: hasattr(cv2, 'data')로 체크 후 사용하거나, 직접 경로를 지정해야 합니다.
            
            # 1. 프로젝트 models/haarcascades 폴더 우선 시도
            opencv_haarcascade_path = None
            if os.path.exists(os.path.join('models', 'haarcascades')):
                opencv_haarcascade_path = os.path.join('models', 'haarcascades')
            # 2. 사용자 지정 cascade_dir 인자가 있으면 그 경로도 시도
            elif cascade_dir and os.path.exists(cascade_dir):
                opencv_haarcascade_path = cascade_dir
            # 3. 마지막으로 OpenCV 설치 경로에서 찾기
            else:
                possible_paths = [
                    os.path.join(os.path.dirname(cv2.__file__), 'data', 'haarcascades'),
                    os.path.join(os.path.dirname(cv2.__file__), '..', 'data', 'haarcascades'),
                    'C:/opencv/build/etc/haarcascades',  # Windows OpenCV 설치 경로
                    '/usr/share/opencv4/haarcascades',   # Linux OpenCV 경로
                    '/usr/local/share/opencv4/haarcascades'  # macOS OpenCV 경로
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        opencv_haarcascade_path = path
                        break

            if opencv_haarcascade_path:
                try:
                    cascade_files = {
                        'face': 'haarcascade_frontalface_default.xml',
                        'eye': 'haarcascade_eye.xml',
                        'fullbody': 'haarcascade_fullbody.xml',
                        'upperbody': 'haarcascade_upperbody.xml'
                    }
                    for name, filename in cascade_files.items():
                        path = os.path.join(opencv_haarcascade_path, filename)
                        if os.path.exists(path):
                            self.cascades[name] = cv2.CascadeClassifier(path)
                            print(f"✅ {name} cascade 로드 성공: {path}")
                        else:
                            print(f"⚠️ {name} cascade 파일 없음: {path}")
                    print(f"✅ OpenCV cascade 로드 완료 (경로: {opencv_haarcascade_path})")
                except Exception as e:
                    print(f"❌ OpenCV cascade 로드 중 오류: {e}")
            else:
                print("⚠️ OpenCV cascade 경로를 찾을 수 없습니다.")
                    
        except Exception as e:
            print(f"❌ OpenCV cascade 로드 실패: {e}")
        
        # 4. 사용자 지정 cascade 디렉토리도 시도 (아직 로드되지 않은 경우)
        if cascade_dir and os.path.exists(cascade_dir):
            print(f"🔍 사용자 cascade 디렉토리 확인: {cascade_dir}")
            user_cascade_files = {
                'face': 'haarcascade_frontalface_default.xml',
                'eye': 'haarcascade_eye.xml',
                'fullbody': 'haarcascade_fullbody.xml',
                'upperbody': 'haarcascade_upperbody.xml'
            }
            
            for name, filename in user_cascade_files.items():
                if name not in self.cascades:  # 아직 로드되지 않은 경우만
                    path = os.path.join(cascade_dir, filename)
                    if os.path.exists(path):
                        self.cascades[name] = cv2.CascadeClassifier(path)
                        print(f"✅ 사용자 {name} cascade 로드 성공: {path}")

    def detect(self, frame, cascade_name='face'):
        """
        지정한 cascade로 객체 검출
        frame: 입력 이미지 (BGR)
        cascade_name: 사용할 cascade 이름 (face, eye 등)
        return: 검출된 객체 리스트
        """
        if cascade_name not in self.cascades:
            print(f"⚠️ {cascade_name} cascade가 로드되지 않았습니다.")
            return []
            
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            objects = self.cascades[cascade_name].detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=4,
                minSize=(30, 30)
            )
            return objects
        except Exception as e:
            print(f"❌ {cascade_name} 탐지 중 오류: {e}")
            return []

    def detect_yolo_objects(self, frame):
        """
        YOLO 모델을 사용해서 객체 탐지 (OpenCV 방식)
        frame: 입력 이미지 (BGR)
        return: YOLO 탐지 결과
        """
        if self.yolo_model is None:
            return None
            
        try:
            # YOLO 모델로 탐지
            results = self.yolo_model(frame, verbose=False)
            return results
        except Exception as e:
            print(f"❌ OpenCV YOLO 탐지 중 오류: {e}")
            return None 