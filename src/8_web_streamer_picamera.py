# /home/pi/autocarz/src/8_web_streamer_picamera.py
from flask import Flask, Response, render_template, request, jsonify
from picamera2 import Picamera2
import cv2
import time
import threading
from queue import Queue
import numpy as np
import json
import os

app = Flask(__name__, 
           template_folder='/home/pi/autocarz/templates',
           static_folder='/home/pi/autocarz/static')

# 전역 변수
model = None
yolo_available = False
opencv_cascades = {}

# 설정 파일 경로
SETTINGS_FILE = "/home/pi/autocarz/camera_settings.json"

# 기본 설정
flip_settings = {
    "horizontal": False,
    "vertical": False,
    "rotation": 0
}

detection_settings = {
    "yolo_enabled": True,
    "opencv_enabled": True,
    "show_fps": True,
    "resolution": "1024x768",
    "quality": 85,
    "fps_limit": 15
}

# FPS 계산용 변수
fps_counter = 0
fps_start_time = time.time()
current_fps = 0

def load_settings():
    """설정 파일에서 설정 로드"""
    global flip_settings, detection_settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                if 'flip_settings' in loaded_settings:
                    flip_settings.update(loaded_settings['flip_settings'])
                else:
                    flip_settings.update(loaded_settings)
                
                if 'detection_settings' in loaded_settings:
                    detection_settings.update(loaded_settings['detection_settings'])
                
                print(f"설정 로드 완료: {flip_settings}")
    except Exception as e:
        print(f"설정 로드 에러: {e}")

def save_settings():
    """설정을 파일에 저장"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        settings_data = flip_settings.copy()
        settings_data['detection_settings'] = detection_settings
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)
        print("설정 저장 완료")
    except Exception as e:
        print(f"설정 저장 에러: {e}")

def apply_flip_transform(frame):
    """프레임에 반전 및 회전 적용"""
    try:
        if flip_settings["horizontal"]:
            frame = cv2.flip(frame, 1)
        
        if flip_settings["vertical"]:
            frame = cv2.flip(frame, 0)
        
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

def get_resolution_from_setting():
    """설정에서 해상도 추출"""
    resolution_str = detection_settings.get("resolution", "1024x768")
    try:
        width, height = map(int, resolution_str.split('x'))
        return (width, height)
    except:
        return (1024, 768)

def initialize_opencv_cascades():
    """OpenCV Haar Cascade 초기화"""
    global opencv_cascades
    
    try:
        face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(face_cascade_path):
            opencv_cascades['face'] = cv2.CascadeClassifier(face_cascade_path)
            print("OpenCV 얼굴 검출 캐스케이드 로드 완료")
        
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
    """OpenCV로 객체 검출"""
    detections = []
    
    try:
        height, width = frame_bgr.shape[:2]
        scale_factor = 0.5 if width > 640 else 1.0
        
        if scale_factor < 1.0:
            small_frame = cv2.resize(frame_bgr, (int(width * scale_factor), int(height * scale_factor)))
        else:
            small_frame = frame_bgr
        
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        for cascade_name, cascade in opencv_cascades.items():
            try:
                objects = cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                for (x, y, w, h) in objects:
                    if scale_factor < 1.0:
                        x = int(x / scale_factor)
                        y = int(y / scale_factor)
                        w = int(w / scale_factor)
                        h = int(h / scale_factor)
                    
                    detections.append({
                        'bbox': (x, y, x+w, y+h),
                        'class': cascade_name,
                        'confidence': 0.95
                    })
                    
            except Exception as e:
                print(f"OpenCV {cascade_name} 검출 에러: {e}")
                
    except Exception as e:
        print(f"OpenCV 검출 에러: {e}")
    
    return detections

def draw_yolo_boxes(frame, results):
    """YOLO 검출 결과를 파란색 박스로 그리기 (인코딩 문제 해결)"""
    try:
        if not results or len(results) == 0:
            return frame
            
        result = results[0]
        
        if result.boxes is None or len(result.boxes) == 0:
            return frame
        
        for box in result.boxes:
            try:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                
                # 인코딩 문제 해결: 영어만 사용
                label = f"YOLO-Obj{cls_id}: {conf:.2f}"
                
                # 파란색 박스 그리기
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                )
                
                cv2.rectangle(
                    frame,
                    (x1, y1 - text_height - baseline - 5),
                    (x1 + text_width, y1),
                    (255, 0, 0),
                    -1
                )
                
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - baseline - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
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
            
            # 빨간색 박스 그리기
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            label = f"CV-{class_name}: {confidence:.2f}"
            
            (text_width, text_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            
            cv2.rectangle(
                frame,
                (x1, y1 - text_height - baseline - 5),
                (x1 + text_width, y1),
                (0, 0, 255),
                -1
            )
            
            cv2.putText(
                frame,
                label,
                (x1, y1 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
    
    except Exception as e:
        print(f"OpenCV 박스 그리기 에러: {e}")
    
    return frame

def initialize_yolo_model():
    """YOLO 모델 초기화"""
    global model, yolo_available
    
    try:
        from ultralytics import YOLO
        import numpy as np
        
        model_path = "/home/pi/autocarz/models/best.pt"
        if not os.path.exists(model_path):
            print(f"모델 파일이 존재하지 않습니다: {model_path}")
            yolo_available = False
            return
        
        print(f"YOLO 모델 로드 시도: {model_path}")
        model = YOLO(model_path)
        model.overrides['verbose'] = False
        model.overrides['device'] = 'cpu'
        model.overrides['half'] = False
        
        # 테스트 추론
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        test_frame = np.ascontiguousarray(test_frame)
        
        try:
            with np.errstate(all='ignore'):
                test_results = model.predict(
                    test_frame,
                    verbose=False,
                    conf=0.5,
                    device='cpu',
                    half=False
                )
            
            if test_results:
                print("YOLO 테스트 추론 성공!")
                yolo_available = True
                print("YOLO 모델 로드 완료")
                return
                
        except Exception as inference_error:
            print(f"YOLO 추론 테스트 실패: {inference_error}")
        
        yolo_available = False
        model = None
        print("YOLO 모델 테스트 실패")
        
    except ImportError as e:
        print(f"ultralytics import 실패: {e}")
        yolo_available = False
    except Exception as e:
        print(f"YOLO 모델 로드 실패: {e}")
        yolo_available = False

# 카메라 설정
width, height = get_resolution_from_setting()
picam2 = Picamera2()
picam2.preview_configuration.main.size = (width, height)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(2)

# 프레임 큐
frame_queue = Queue(maxsize=2)
processed_queue = Queue(maxsize=2)

def capture_frames():
    """카메라에서 프레임을 캡처하는 스레드"""
    frame_interval = 1.0 / detection_settings["fps_limit"]
    last_capture_time = 0
    
    while True:
        try:
            current_time = time.time()
            if current_time - last_capture_time < frame_interval:
                time.sleep(0.01)
                continue
                
            frame = picam2.capture_array()
            last_capture_time = current_time
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            if not isinstance(frame, np.ndarray):
                frame = np.array(frame)
            
            if frame.dtype != np.uint8:
                if frame.dtype in [np.float32, np.float64] and frame.max() <= 1.0:
                    frame = (frame * 255).astype(np.uint8)
                else:
                    frame = frame.astype(np.uint8)
            
            if len(frame.shape) != 3 or frame.shape[2] != 3:
                continue
            
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)
            
            frame = apply_flip_transform(frame)
            
            if not frame_queue.full():
                frame_queue.put(frame)
            else:
                try:
                    frame_queue.get_nowait()
                    frame_queue.put(frame)
                except:
                    pass
            
        except Exception as e:
            print(f"카메라 캡처 에러: {e}")
            time.sleep(0.1)

def process_frames():
    """이중 검출 처리"""
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
                if not isinstance(frame, np.ndarray):
                    frame = np.array(frame, dtype=np.uint8)
                
                if len(frame.shape) != 3 or frame.shape[2] != 3:
                    if not processed_queue.full():
                        processed_queue.put(frame)
                    continue
                
                frame = np.clip(frame, 0, 255).astype(np.uint8)
                
                if not frame.flags['C_CONTIGUOUS']:
                    frame = np.ascontiguousarray(frame)
                
                # RGB to BGR 변환
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                frame_bgr = np.ascontiguousarray(frame_bgr)
                result_frame = frame_bgr.copy()
                
                yolo_count = 0
                opencv_count = 0
                
                # YOLO 검출 (파란색)
                if detection_settings["yolo_enabled"] and yolo_available and model is not None:
                    try:
                        with np.errstate(all='ignore'):
                            results = model.predict(
                                frame_bgr,
                                verbose=False,
                                conf=0.5,
                                device='cpu',
                                half=False
                            )
                        
                        if results and len(results) > 0:
                            result_frame = draw_yolo_boxes(result_frame, results)
                            if results[0].boxes is not None:
                                yolo_count = len(results[0].boxes)
                            
                    except Exception as yolo_error:
                        if frame_count % 100 == 0:
                            print(f"YOLO 추론 에러: {yolo_error}")
                
                # OpenCV 검출 (빨간색)
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
                    cv2.putText(result_frame, f"FPS: {current_fps}", (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    info_text = f"YOLO(Blue): {yolo_count} | OpenCV(Red): {opencv_count}"
                    cv2.putText(result_frame, info_text, (10, 60), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # BGR to RGB 변환
                result_frame = cv2.cvtColor(result_frame, cv2.COLOR_BGR2RGB)
                result_frame = np.ascontiguousarray(result_frame)
                
                if not processed_queue.full():
                    processed_queue.put(result_frame)
                else:
                    try:
                        processed_queue.get_nowait()
                        processed_queue.put(result_frame)
                    except:
                        pass
                        
            except Exception as e:
                if frame_count % 100 == 0:
                    print(f"프레임 처리 에러: {e}")
                
                if not processed_queue.full():
                    processed_queue.put(frame)
        
        time.sleep(0.01)

def generate_frames():
    """웹 스트리밍용 프레임 생성"""
    while True:
        if not processed_queue.empty():
            annotated_frame = processed_queue.get()
            
            try:
                frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
                
                encode_param = [cv2.IMWRITE_JPEG_QUALITY, detection_settings["quality"]]
                success, buffer = cv2.imencode(".jpg", frame_bgr, encode_param)
                
                if success:
                    frame_bytes = buffer.tobytes()
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            except Exception as e:
                print(f"프레임 인코딩 에러: {e}")
        else:
            time.sleep(0.01)

# ============= Flask 라우트 =============

@app.route("/")
def index():
    """메인 페이지 - 이제 템플릿 파일 사용"""
    yolo_status = "활성화됨" if yolo_available else "비활성화됨"
    opencv_status = "활성화됨" if len(opencv_cascades) > 0 else "비활성화됨"
    
    return render_template('index.html', 
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
        
        flip_settings["horizontal"] = data.get("horizontal", False)
        flip_settings["vertical"] = data.get("vertical", False)
        flip_settings["rotation"] = data.get("rotation", 0)
        
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
        
        detection_settings["yolo_enabled"] = data.get("yolo_enabled", True)
        detection_settings["opencv_enabled"] = data.get("opencv_enabled", True)
        detection_settings["show_fps"] = data.get("show_fps", True)
        detection_settings["quality"] = data.get("quality", 85)
        detection_settings["fps_limit"] = data.get("fps_limit", 15)
        
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
    print("=== 시스템 초기화 ===")
    
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
    print("🔵 파란색 박스: YOLO 검출 결과")
    print("🔴 빨간색 박스: OpenCV 검출 결과")
    
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)