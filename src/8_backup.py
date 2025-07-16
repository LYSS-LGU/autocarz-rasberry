# /home/pi/autocarz/src/8_web_streamer.py
from flask import Flask, Response, render_template_string, request, jsonify
from PIL import Image, ImageDraw, ImageFont
from picamera2 import Picamera2
import cv2
import time
import threading
from queue import Queue
import numpy as np
import json
import os

app = Flask(__name__)

# 전역 변수
model = None
yolo_available = False
opencv_cascades = {}

# 반전 설정 파일 경로
SETTINGS_FILE = "/home/pi/autocarz/camera_settings.json"

# 기본 반전 설정
flip_settings = {
    "horizontal": False,  # 좌우 반전
    "vertical": False,    # 상하 반전
    "rotation": 0         # 회전 (0, 90, 180, 270)
}

# 검출 모드 설정
detection_settings = {
    "yolo_enabled": True,      # YOLO 검출 활성화 (파란색)
    "opencv_enabled": True,    # OpenCV 검출 활성화 (빨간색)
    "show_fps": True          # FPS 표시
}

def load_settings():
    """설정 파일에서 반전 설정 로드"""
    global flip_settings, detection_settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                loaded_settings = json.load(f)
                # 기존 flip_settings 호환성 유지
                if 'flip_settings' in loaded_settings:
                    flip_settings.update(loaded_settings['flip_settings'])
                else:
                    flip_settings.update(loaded_settings)
                
                # detection_settings 로드
                if 'detection_settings' in loaded_settings:
                    detection_settings.update(loaded_settings['detection_settings'])
                
                print(f"설정 로드 완료: {flip_settings}")
    except Exception as e:
        print(f"설정 로드 에러: {e}")

def save_settings():
    """설정을 파일에 저장"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        # 기존 호환성 유지를 위해 flip_settings를 최상위에 저장
        settings_data = flip_settings.copy()
        settings_data['detection_settings'] = detection_settings
        
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_data, f, indent=2)
        print(f"설정 저장 완료: {settings_data}")
    except Exception as e:
        print(f"설정 저장 에러: {e}")

def apply_flip_transform(frame):
    """프레임에 반전 및 회전 적용"""
    try:
        # 좌우 반전 (수평)
        if flip_settings["horizontal"]:
            frame = cv2.flip(frame, 1)
        
        # 상하 반전 (수직)
        if flip_settings["vertical"]:
            frame = cv2.flip(frame, 0)
        
        # 회전 적용
        rotation = flip_settings["rotation"]
        if rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        return frame
    except Exception as e:
        print(f"반전 적용 에러: {e}")
        return frame

def initialize_opencv_cascades():
    """OpenCV Haar Cascade 초기화"""
    global opencv_cascades
    
    try:
        # 얼굴 검출 캐스케이드
        face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(face_cascade_path):
            opencv_cascades['face'] = cv2.CascadeClassifier(face_cascade_path)
            print("OpenCV 얼굴 검출 캐스케이드 로드 완료")
        
        # 눈 검출 캐스케이드
        eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        if os.path.exists(eye_cascade_path):
            opencv_cascades['eye'] = cv2.CascadeClassifier(eye_cascade_path)
            print("OpenCV 눈 검출 캐스케이드 로드 완료")
        
        print(f"OpenCV 캐스케이드 로드 완료: {list(opencv_cascades.keys())}")
        return len(opencv_cascades) > 0
        
    except Exception as e:
        print(f"OpenCV 캐스케이드 로드 실패: {e}")
        return False

def opencv_detect_objects(frame_bgr):
    """OpenCV로 객체 검출 (빨간색 박스로 표시할 예정)"""
    detections = []
    
    try:
        # BGR to Gray 변환
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        
        # 각 캐스케이드로 검출
        for cascade_name, cascade in opencv_cascades.items():
            try:
                objects = cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                for (x, y, w, h) in objects:
                    detections.append({
                        'bbox': (x, y, x+w, y+h),
                        'class': cascade_name,
                        'confidence': 0.95  # OpenCV는 신뢰도를 제공하지 않으므로 고정값
                    })
                    
            except Exception as e:
                print(f"OpenCV {cascade_name} 검출 에러: {e}")
                
    except Exception as e:
        print(f"OpenCV 검출 에러: {e}")
    
    return detections

def draw_yolo_boxes(frame, results):
    """YOLO 검출 결과를 파란색 박스로 그리기"""
    try:
        if not results or len(results) == 0:
            return frame
            
        result = results[0]
        
        # 박스 정보가 있는지 확인
        if result.boxes is None or len(result.boxes) == 0:
            return frame
        
        # 각 박스에 대해 처리
        for box in result.boxes:
            try:
                # 박스 좌표 (xyxy 형식)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                
                # 신뢰도
                conf = float(box.conf[0].cpu().numpy())
                
                # 클래스 ID
                cls_id = int(box.cls[0].cpu().numpy())
                
                # 클래스 이름 (한글 처리)
                class_names = result.names
                if cls_id in class_names:
                    class_name = class_names[cls_id]
                else:
                    class_name = f"Class_{cls_id}"
                
                # YOLO 박스 그리기 (파란색)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # BGR에서 파란색
                
                # 레이블 텍스트 (영어만 사용하여 인코딩 문제 방지)
                if isinstance(class_name, str):
                    try:
                        class_name.encode('ascii')
                        label = f"YOLO-{class_name}: {conf:.2f}"
                    except UnicodeEncodeError:
                        label = f"YOLO-Obj{cls_id}: {conf:.2f}"
                else:
                    label = f"YOLO-Obj{cls_id}: {conf:.2f}"
                
                # 텍스트 배경 박스 크기 계산
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                )
                
                # 텍스트 배경 박스 그리기 (파란색)
                cv2.rectangle(
                    frame,
                    (x1, y1 - text_height - baseline - 5),
                    (x1 + text_width, y1),
                    (255, 0, 0),  # BGR에서 파란색
                    -1
                )
                
                # 텍스트 그리기 (흰색)
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - baseline - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),  # 흰색
                    2
                )
                
            except Exception as box_error:
                print(f"YOLO 박스 그리기 에러: {box_error}")
                continue
        
        return frame
        
    except Exception as e:
        print(f"YOLO 박스 그리기 에러: {e}")
        return frame

def draw_opencv_boxes(frame, detections):
    """OpenCV 검출 결과를 빨간색 박스로 그리기"""
    try:
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            class_name = detection['class']
            confidence = detection['confidence']
            
            # OpenCV 박스 그리기 (빨간색)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # BGR에서 빨간색
            
            # 레이블 텍스트
            label = f"CV-{class_name}: {confidence:.2f}"
            
            # 텍스트 배경 박스 크기 계산
            (text_width, text_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            
            # 텍스트 배경 박스 그리기 (빨간색)
            cv2.rectangle(
                frame,
                (x1, y1 - text_height - baseline - 5),
                (x1 + text_width, y1),
                (0, 0, 255),  # BGR에서 빨간색
                -1
            )
            
            # 텍스트 그리기 (흰색)
            cv2.putText(
                frame,
                label,
                (x1, y1 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),  # 흰색
                2
            )
    
    except Exception as e:
        print(f"OpenCV 박스 그리기 에러: {e}")
    
    return frame

def check_numpy_compatibility():
    """numpy 호환성 확인"""
    try:
        import numpy as np
        print(f"NumPy 버전: {np.__version__}")
        
        # 기본 테스트
        test_array = np.zeros((100, 100, 3), dtype=np.uint8)
        test_array = np.ascontiguousarray(test_array)
        
        print("NumPy 기본 테스트 통과")
        return True
        
    except Exception as e:
        print(f"NumPy 호환성 문제: {e}")
        return False

def initialize_yolo_model():
    """YOLO 모델 초기화 - numpy 호환성 문제 해결"""
    global model, yolo_available
    
    try:
        from ultralytics import YOLO
        import numpy as np
        
        # 모델 경로 확인
        model_path = "/home/pi/autocarz/models/best.pt"
        if not os.path.exists(model_path):
            print(f"모델 파일이 존재하지 않습니다: {model_path}")
            yolo_available = False
            return
        
        print(f"YOLO 모델 로드 시도: {model_path}")
        
        # 모델 로드
        model = YOLO(model_path)
        
        # 모델 설정
        model.overrides['verbose'] = False
        model.overrides['device'] = 'cpu'
        model.overrides['half'] = False
        
        # 테스트 추론 - numpy 호환성 문제 해결
        print("테스트 추론 시작...")
        
        # 명시적으로 numpy 배열 생성 (호환성 확보)
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 메모리 연속성 확보
        test_frame = np.ascontiguousarray(test_frame)
        
        # 안전한 추론 실행
        try:
            with np.errstate(all='ignore'):  # numpy 경고 무시
                test_results = model.predict(
                    test_frame,
                    verbose=False,
                    conf=0.5,
                    device='cpu',
                    half=False,
                    augment=False,
                    agnostic_nms=False
                )
            
            if test_results:
                print("테스트 추론 성공!")
                yolo_available = True
                print("YOLO 모델 로드 완료")
                return
            else:
                print("테스트 추론 결과가 비어있습니다")
                
        except Exception as inference_error:
            print(f"추론 테스트 실패: {inference_error}")
            
            # 대안: 더 간단한 테스트
            try:
                print("간단한 테스트 시도...")
                simple_test = np.ones((320, 320, 3), dtype=np.uint8) * 128
                simple_test = np.ascontiguousarray(simple_test)
                
                test_results = model(simple_test, verbose=False)
                if test_results:
                    print("간단한 테스트 성공!")
                    yolo_available = True
                    print("YOLO 모델 로드 완료 (간단한 테스트)")
                    return
                    
            except Exception as simple_error:
                print(f"간단한 테스트도 실패: {simple_error}")
        
        # 모든 테스트 실패
        yolo_available = False
        model = None
        print("YOLO 모델 테스트 실패 - 원본 영상만 표시됩니다")
        
    except ImportError as e:
        print(f"ultralytics import 실패: {e}")
        yolo_available = False
    except Exception as e:
        print(f"YOLO 모델 로드 실패: {e}")
        print(f"에러 타입: {type(e).__name__}")
        
        # 추가 디버깅 정보
        try:
            import traceback
            print("상세 에러 정보:")
            traceback.print_exc()
        except:
            pass
            
        yolo_available = False

# 카메라 설정
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(2)

# 프레임 큐
frame_queue = Queue(maxsize=2)
processed_queue = Queue(maxsize=2)

# FPS 계산용 변수
fps_counter = 0
fps_start_time = time.time()
current_fps = 0

def capture_frames():
    """카메라에서 프레임을 캡처하는 스레드 - 개선된 버전"""
    while True:
        try:
            # 카메라에서 프레임 캡처
            frame = picam2.capture_array()
            
            # 프레임 유효성 검사
            if frame is None:
                print("캡처된 프레임이 None입니다")
                time.sleep(0.1)
                continue
            
            # numpy 배열 확인 및 변환
            if not isinstance(frame, np.ndarray):
                print(f"프레임이 numpy 배열이 아닙니다: {type(frame)}")
                frame = np.array(frame)
            
            # 데이터 타입 확인
            if frame.dtype != np.uint8:
                if frame.dtype == np.float32 or frame.dtype == np.float64:
                    # 0-1 범위라면 0-255로 변환
                    if frame.max() <= 1.0:
                        frame = (frame * 255).astype(np.uint8)
                    else:
                        frame = frame.astype(np.uint8)
                else:
                    frame = frame.astype(np.uint8)
            
            # 프레임 차원 확인
            if len(frame.shape) != 3:
                print(f"잘못된 프레임 차원: {frame.shape}")
                continue
            
            # RGB 채널 확인
            if frame.shape[2] != 3:
                print(f"RGB 채널이 3개가 아닙니다: {frame.shape[2]}")
                continue
            
            # 메모리 연속성 확인
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)
            
            # 반전 및 회전 적용
            frame = apply_flip_transform(frame)
            
            # 큐에 프레임 추가
            if not frame_queue.full():
                frame_queue.put(frame)
            else:
                # 큐가 가득 찬 경우 오래된 프레임 제거
                try:
                    frame_queue.get_nowait()
                    frame_queue.put(frame)
                except:
                    pass
            
            time.sleep(0.03)
            
        except Exception as e:
            print(f"카메라 캡처 에러: {e}")
            time.sleep(0.1)

def process_frames():
    """이중 검출 처리 (YOLO 파란색 + OpenCV 빨간색)"""
    global fps_counter, fps_start_time, current_fps
    frame_count = 0
    
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            frame_count += 1
            
            # FPS 계산
            fps_counter += 1
            if time.time() - fps_start_time >= 1.0:
                current_fps = fps_counter
                fps_counter = 0
                fps_start_time = time.time()
            
            try:
                # 프레임 전처리 - numpy 호환성 확보
                if not isinstance(frame, np.ndarray):
                    frame = np.array(frame, dtype=np.uint8)
                
                # 차원 및 타입 검증
                if len(frame.shape) != 3 or frame.shape[2] != 3:
                    print(f"잘못된 프레임 차원: {frame.shape}")
                    if not processed_queue.full():
                        processed_queue.put(frame)
                    continue
                
                # 데이터 타입 정규화
                if frame.dtype != np.uint8:
                    if frame.dtype in [np.float32, np.float64]:
                        if frame.max() <= 1.0:
                            frame = (frame * 255).astype(np.uint8)
                        else:
                            frame = np.clip(frame, 0, 255).astype(np.uint8)
                    else:
                        frame = frame.astype(np.uint8)
                
                # 픽셀 값 범위 확인
                frame = np.clip(frame, 0, 255).astype(np.uint8)
                
                # 메모리 연속성 확보
                if not frame.flags['C_CONTIGUOUS']:
                    frame = np.ascontiguousarray(frame)
                
                # RGB to BGR 변환
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                frame_bgr = np.ascontiguousarray(frame_bgr)
                
                # 결과 프레임 초기화
                result_frame = frame_bgr.copy()
                
                yolo_count = 0
                opencv_count = 0
                
                # YOLO 검출 (파란색 박스)
                if detection_settings["yolo_enabled"] and yolo_available and model is not None:
                    try:
                        with np.errstate(all='ignore'):
                            results = model.predict(
                                frame_bgr,
                                verbose=False,
                                conf=0.5,
                                device='cpu',
                                half=False,
                                augment=False,
                                agnostic_nms=False,
                                max_det=100
                            )
                        
                        if results and len(results) > 0:
                            result_frame = draw_yolo_boxes(result_frame, results)
                            if results[0].boxes is not None:
                                yolo_count = len(results[0].boxes)
                            
                    except Exception as yolo_error:
                        if frame_count % 100 == 0:  # 너무 많은 로그 방지
                            print(f"YOLO 추론 에러: {yolo_error}")
                
                # OpenCV 검출 (빨간색 박스)
                if detection_settings["opencv_enabled"] and len(opencv_cascades) > 0:
                    try:
                        opencv_detections = opencv_detect_objects(result_frame)
                        opencv_count = len(opencv_detections)
                        
                        if opencv_detections:
                            result_frame = draw_opencv_boxes(result_frame, opencv_detections)
                            
                    except Exception as opencv_error:
                        if frame_count % 100 == 0:
                            print(f"OpenCV 검출 에러: {opencv_error}")
                
                # FPS 및 검출 정보 표시
                if detection_settings["show_fps"]:
                    # FPS 표시
                    cv2.putText(result_frame, f"FPS: {current_fps}", (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    # 검출 개수 표시
                    info_text = f"YOLO(Blue): {yolo_count} | OpenCV(Red): {opencv_count}"
                    cv2.putText(result_frame, info_text, (10, 60), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # BGR to RGB 변환
                result_frame = cv2.cvtColor(result_frame, cv2.COLOR_BGR2RGB)
                result_frame = np.ascontiguousarray(result_frame)
                
                # 큐에 결과 추가
                if not processed_queue.full():
                    processed_queue.put(result_frame)
                else:
                    # 큐가 가득 찬 경우 오래된 프레임 제거
                    try:
                        processed_queue.get_nowait()
                        processed_queue.put(result_frame)
                    except:
                        pass
                        
            except Exception as e:
                if frame_count % 100 == 0:  # 너무 많은 로그 방지
                    print(f"프레임 처리 에러: {e}")
                
                # 에러 시 원본 프레임 사용
                if not processed_queue.full():
                    processed_queue.put(frame)
        
        time.sleep(0.01)

def generate_frames():
    """웹 스트리밍용 프레임 생성"""
    while True:
        if not processed_queue.empty():
            annotated_frame = processed_queue.get()
            
            try:
                # RGB to BGR 변환 (JPEG 인코딩용)
                frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
                
                # JPEG 압축
                encode_param = [cv2.IMWRITE_JPEG_QUALITY, 75]
                success, buffer = cv2.imencode(".jpg", frame_bgr, encode_param)
                
                if success:
                    frame_bytes = buffer.tobytes()
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            except Exception as e:
                print(f"프레임 인코딩 에러: {e}")
        else:
            time.sleep(0.01)

@app.route("/")
def index():
    yolo_status = "활성화됨" if yolo_available else "비활성화됨"
    opencv_status = "활성화됨" if len(opencv_cascades) > 0 else "비활성화됨"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>YOLO + OpenCV 이중 검출 스트리밍</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .video-container { text-align: center; margin: 20px 0; }
            .controls { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .control-group { margin: 10px 0; }
            .control-group label { display: inline-block; width: 150px; }
            button { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-warning { background: #ffc107; color: black; }
            .btn-danger { background: #dc3545; color: white; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .status.success { background: #d4edda; border: 1px solid #c3e6cb; }
            .status.error { background: #f8d7da; border: 1px solid #f5c6cb; }
            .status.info { background: #d1ecf1; border: 1px solid #bee5eb; }
            input[type="checkbox"] { margin-right: 8px; }
            select { padding: 5px; margin-left: 10px; }
            .legend { background: #e9ecef; padding: 15px; border-radius: 8px; margin: 20px 0; }
            .legend-item { display: inline-block; margin: 5px 15px; }
            .color-box { display: inline-block; width: 20px; height: 20px; margin-right: 5px; vertical-align: middle; border: 1px solid #000; }
            .blue-box { background-color: blue; }
            .red-box { background-color: red; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 YOLO + OpenCV 이중 검출 스트리밍</h1>
            
            <div class="status info">
                <p><strong>YOLO 상태:</strong> {{ yolo_status }}</p>
                <p><strong>OpenCV 상태:</strong> {{ opencv_status }}</p>
                <p><strong>카메라:</strong> Pi Camera v2 (640x480)</p>
                <p><strong>성능 비교:</strong> 실시간 이중 검출 + 딜레이 측정</p>
            </div>
            
            <div class="legend">
                <h3>🎨 검출 결과 색상 구분</h3>
                <div class="legend-item">
                    <span class="color-box blue-box"></span>
                    <strong>파란색 박스:</strong> YOLO v8 검출 결과
                </div>
                <div class="legend-item">
                    <span class="color-box red-box"></span>
                    <strong>빨간색 박스:</strong> OpenCV Haar Cascade 검출 결과
                </div>
            </div>
            
            <div class="controls">
                <h3>🎛️ 검출 설정</h3>
                
                <div class="control-group">
                    <label>
                        <input type="checkbox" id="yolo_enabled" {{ 'checked' if detection_settings.yolo_enabled else '' }}>
                        YOLO 검출 활성화 (파란색)
                    </label>
                </div>
                
                <div class="control-group">
                    <label>
                        <input type="checkbox" id="opencv_enabled" {{ 'checked' if detection_settings.opencv_enabled else '' }}>
                        OpenCV 검출 활성화 (빨간색)
                    </label>
                </div>
                
                <div class="control-group">
                    <label>
                        <input type="checkbox" id="show_fps" {{ 'checked' if detection_settings.show_fps else '' }}>
                        FPS 및 검출 정보 표시
                    </label>
                </div>
                
                <button class="btn-primary" onclick="applyDetectionSettings()">검출 설정 적용</button>
            </div>
            
            <div class="controls">
                <h3>📹 카메라 설정</h3>
                
                <div class="control-group">
                    <label>
                        <input type="checkbox" id="horizontal" {{ 'checked' if flip_settings.horizontal else '' }}>
                        좌우 반전
                    </label>
                </div>
                
                <div class="control-group">
                    <label>
                        <input type="checkbox" id="vertical" {{ 'checked' if flip_settings.vertical else '' }}>
                        상하 반전
                    </label>
                </div>
                
                <div class="control-group">
                    <label>회전:</label>
                    <select id="rotation">
                        <option value="0" {{ 'selected' if flip_settings.rotation == 0 else '' }}>0°</option>
                        <option value="90" {{ 'selected' if flip_settings.rotation == 90 else '' }}>90°</option>
                        <option value="180" {{ 'selected' if flip_settings.rotation == 180 else '' }}>180°</option>
                        <option value="270" {{ 'selected' if flip_settings.rotation == 270 else '' }}>270°</option>
                    </select>
                </div>
                
                <button class="btn-primary" onclick="applySettings()">카메라 설정 적용</button>
                <button class="btn-warning" onclick="resetSettings()">전체 초기화</button>
            </div>
            
            <div id="message" class="status" style="display: none;"></div>
            
            <div class="video-container">
                <h3>📺 실시간 이중 검출 스트리밍</h3>
                <img src="/video_feed" style="max-width: 100%; border: 2px solid #ddd; border-radius: 8px;">
            </div>
            
            <div class="controls">
                <h3>🎮 빠른 설정</h3>
                <button class="btn-primary" onclick="setFlip('normal')">정상</button>
                <button class="btn-primary" onclick="setFlip('horizontal')">좌우 반전</button>
                <button class="btn-primary" onclick="setFlip('vertical')">상하 반전</button>
                <button class="btn-primary" onclick="setFlip('both')">상하좌우 반전</button>
                <button class="btn-primary" onclick="setFlip('rotate180')">180° 회전</button>
            </div>
        </div>
        
        <script>
            // 검출 설정 적용
            function applyDetectionSettings() {
                const detection_settings = {
                    yolo_enabled: document.getElementById('yolo_enabled').checked,
                    opencv_enabled: document.getElementById('opencv_enabled').checked,
                    show_fps: document.getElementById('show_fps').checked
                };
                
                fetch('/update_detection_settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(detection_settings)
                })
                .then(response => response.json())
                .then(data => {
                    showMessage(data.message, data.success ? 'success' : 'error');
                });
            }
            
            // 카메라 설정 적용
            function applySettings() {
                const settings = {
                    horizontal: document.getElementById('horizontal').checked,
                    vertical: document.getElementById('vertical').checked,
                    rotation: parseInt(document.getElementById('rotation').value)
                };
                
                fetch('/update_settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings)
                })
                .then(response => response.json())
                .then(data => {
                    showMessage(data.message, data.success ? 'success' : 'error');
                });
            }
            
            function resetSettings() {
                document.getElementById('horizontal').checked = false;
                document.getElementById('vertical').checked = false;
                document.getElementById('rotation').value = '0';
                document.getElementById('yolo_enabled').checked = true;
                document.getElementById('opencv_enabled').checked = true;
                document.getElementById('show_fps').checked = true;
                applySettings();
                applyDetectionSettings();
            }
            
            function setFlip(type) {
                switch(type) {
                    case 'normal':
                        document.getElementById('horizontal').checked = false;
                        document.getElementById('vertical').checked = false;
                        document.getElementById('rotation').value = '0';
                        break;
                    case 'horizontal':
                        document.getElementById('horizontal').checked = true;
                        document.getElementById('vertical').checked = false;
                        document.getElementById('rotation').value = '0';
                        break;
                    case 'vertical':
                        document.getElementById('horizontal').checked = false;
                        document.getElementById('vertical').checked = true;
                        document.getElementById('rotation').value = '0';
                        break;
                    case 'both':
                        document.getElementById('horizontal').checked = true;
                        document.getElementById('vertical').checked = true;
                        document.getElementById('rotation').value = '0';
                        break;
                    case 'rotate180':
                        document.getElementById('horizontal').checked = false;
                        document.getElementById('vertical').checked = false;
                        document.getElementById('rotation').value = '180';
                        break;
                }
                applySettings();
            }
            
            function showMessage(msg, type) {
                const messageDiv = document.getElementById('message');
                messageDiv.textContent = msg;
                messageDiv.className = 'status ' + type;
                messageDiv.style.display = 'block';
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 3000);
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html_template, 
                                  yolo_status=yolo_status, 
                                  opencv_status=opencv_status,
                                  flip_settings=flip_settings,
                                  detection_settings=detection_settings)

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/update_settings", methods=["POST"])
def update_settings():
    """카메라 반전 설정 업데이트"""
    try:
        global flip_settings
        data = request.get_json()
        
        # 설정 업데이트
        flip_settings["horizontal"] = data.get("horizontal", False)
        flip_settings["vertical"] = data.get("vertical", False)
        flip_settings["rotation"] = data.get("rotation", 0)
        
        # 설정 저장
        save_settings()
        
        return jsonify({
            "success": True,
            "message": "카메라 설정이 성공적으로 적용되었습니다!",
            "settings": flip_settings
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"카메라 설정 적용 실패: {str(e)}"
        })

@app.route("/update_detection_settings", methods=["POST"])
def update_detection_settings():
    """검출 설정 업데이트"""
    try:
        global detection_settings
        data = request.get_json()
        
        # 설정 업데이트
        detection_settings["yolo_enabled"] = data.get("yolo_enabled", True)
        detection_settings["opencv_enabled"] = data.get("opencv_enabled", True)
        detection_settings["show_fps"] = data.get("show_fps", True)
        
        # 설정 저장
        save_settings()
        
        return jsonify({
            "success": True,
            "message": "검출 설정이 성공적으로 적용되었습니다!",
            "settings": detection_settings
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"검출 설정 적용 실패: {str(e)}"
        })

@app.route("/get_settings")
def get_settings():
    """현재 설정 반환"""
    return jsonify({
        "flip_settings": flip_settings,
        "detection_settings": detection_settings
    })

@app.route("/reset_settings")
def reset_settings():
    """설정 초기화"""
    global flip_settings, detection_settings
    flip_settings = {
        "horizontal": False,
        "vertical": False,
        "rotation": 0
    }
    detection_settings = {
        "yolo_enabled": True,
        "opencv_enabled": True,
        "show_fps": True
    }
    save_settings()
    return jsonify({
        "success": True,
        "message": "모든 설정이 초기화되었습니다.",
        "flip_settings": flip_settings,
        "detection_settings": detection_settings
    })

@app.route("/status")
def status():
    """시스템 상태 확인"""
    return jsonify({
        "yolo_available": yolo_available,
        "opencv_available": len(opencv_cascades) > 0,
        "model_loaded": model is not None,
        "frame_queue_size": frame_queue.qsize(),
        "processed_queue_size": processed_queue.qsize(),
        "flip_settings": flip_settings,
        "detection_settings": detection_settings,
        "current_fps": current_fps
    })

if __name__ == "__main__":
    print("=== 시스템 호환성 확인 ===")
    
    # NumPy 호환성 확인
    if not check_numpy_compatibility():
        print("NumPy 호환성 문제가 있습니다. 재설치를 권장합니다.")
        print("pip install --upgrade numpy")
    
    # 설정 로드
    load_settings()
    
    # YOLO 모델 초기화
    initialize_yolo_model()
    
    # OpenCV 캐스케이드 초기화
    opencv_available = initialize_opencv_cascades()
    
    # 백그라운드 스레드 시작
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    process_thread = threading.Thread(target=process_frames, daemon=True)
    
    capture_thread.start()
    process_thread.start()
    
    yolo_status = "활성화됨" if yolo_available else "비활성화됨"
    opencv_status = "활성화됨" if opencv_available else "비활성화됨"
    
    print(f"YOLO 상태: {yolo_status}")
    print(f"OpenCV 상태: {opencv_status}")
    print("스트리밍 시작: http://192.168.14.63:5000")
    print("로컬 접속: http://localhost:5000")
    print(f"현재 반전 설정: {flip_settings}")
    print(f"현재 검출 설정: {detection_settings}")
    print("🔵 파란색 박스: YOLO 검출 결과")
    print("🔴 빨간색 박스: OpenCV 검출 결과")
    
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)