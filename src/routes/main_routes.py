# ~/Desktop/autocarz(라파다운로드본)/src/routes/main_routes.py
# 메인 페이지(/), 비디오 피드(/video_feed) 라우트 담당
# 실시간 영상 스트리밍 및 메인 UI 렌더링 (윈도우 버전)

from flask import Blueprint, render_template, Response, request, jsonify
from camera.camera_manager import camera_manager
import platform
import psutil

main_bp = Blueprint('main', __name__)

def get_detection_settings():
    """
    윈도우 환경에 맞는 detection_settings 반환
    """
    return {
        'resolution': '1280x720',           # 일반 웹캠 해상도
        'fps': 30,                          # 초당 프레임 수
        'confidence': 0.5,                  # 객체 탐지 신뢰도
        'model': 'YOLOv8',                  # ultralytics 패키지 사용
        'camera_type': 'USB Webcam',        # PC 웹캠
        'yolo_enabled': True,               # YOLO 검출 활성화
        'opencv_enabled': True,             # OpenCV 검출 활성화
        'show_fps': True,                   # FPS 표시
        'quality': 85,                      # JPEG 품질
        'fps_limit': 30                     # FPS 제한
    }

def get_system_info():
    """
    윈도우 시스템 정보 가져오기
    """
    try:
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        
        # 디스크 사용률 (C: 드라이브)
        disk = psutil.disk_usage('C:\\')
        
        return {
            'status': 'Running',
            'platform': platform.system(),     # Windows
            'cpu_usage': f'{cpu_percent}%',
            'memory_usage': f'{memory.percent}%',
            'disk_usage': f'{(disk.used / disk.total * 100):.1f}%',
            'python_version': platform.python_version()
        }
    except Exception as e:
        print(f"시스템 정보 가져오기 오류: {e}")
        return {
            'status': 'Running',
            'platform': 'Windows',
            'cpu_usage': 'N/A',
            'memory_usage': 'N/A',
            'disk_usage': 'N/A',
            'python_version': 'N/A'
        }

def get_camera_name(index):
    """
    카메라 인덱스에 따른 이름 반환
    """
    camera_names = {
        0: "내장 웹캠 (HD Webcam)",
        1: "외장 웹캠 (SC-FD110B)",
        2: "카메라 2",
        3: "카메라 3",
        4: "카메라 4",
        5: "카메라 5"
    }
    return camera_names.get(index, f"카메라 {index}")

@main_bp.route("/")
def index():
    """
    메인 페이지 라우트 (윈도우 버전)
    - yolo_opencv.html 템플릿 렌더링
    - 윈도우 환경에 맞는 설정 정보 전달
    """
    # 윈도우 환경용 detection_settings
    detection_settings = get_detection_settings()
    
    # 윈도우 시스템 정보
    system_info = get_system_info()
    
    # 현재 카메라 정보 가져오기
    current_camera_index = getattr(camera_manager, 'camera_index', 0)
    current_camera_name = get_camera_name(current_camera_index)
    
    # 카메라 정보 (윈도우 웹캠)
    camera_info = {
        'name': current_camera_name,
        'type': 'USB Webcam',
        'driver': 'DirectShow',              # 윈도우 기본 드라이버
        'index': current_camera_index
    }
    
    # 템플릿에 전달할 모든 데이터 (yolo_opencv.html에서 사용하는 변수들과 일치)
    context = {
        'yolo_status': 'Ready',              # YOLO 상태
        'opencv_status': 'Ready',            # OpenCV 상태
        'detection_settings': detection_settings,
        'flip_settings': {                   # 이미지 반전 설정
            'horizontal': False,
            'vertical': False,
            'rotation': 0
        },
        'color_correction_settings': {       # 색상 보정 설정
            'enabled': False,
            'red_reduction': 1.0,
            'green_boost': 1.0,
            'blue_boost': 1.0,
            'mode': 'standard'
        },
        'system_info': system_info,
        'camera_info': camera_info
    }
    
    return render_template('yolo_opencv.html', **context)

@main_bp.route("/video_feed")
def video_feed():
    """
    실시간 영상 스트리밍 라우트 (윈도우 웹캠)
    - multipart/x-mixed-replace 방식으로 프레임 전송
    - <img src="/video_feed">로 웹에서 실시간 영상 표시
    """
    return Response(camera_manager.generate_frames(), 
                   mimetype="multipart/x-mixed-replace; boundary=frame")

@main_bp.route("/get_current_camera")
def get_current_camera():
    """
    현재 사용 중인 카메라 정보 반환
    """
    try:
        current_index = getattr(camera_manager, 'camera_index', 0)
        current_name = get_camera_name(current_index)
        is_running = getattr(camera_manager, 'is_running', False)
        
        return jsonify({
            'success': True,
            'camera_index': current_index,
            'camera_name': current_name,
            'is_running': is_running
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@main_bp.route("/switch_camera", methods=['POST'])
def switch_camera_route():
    """
    카메라 전환 라우트
    """
    try:
        data = request.get_json()
        camera_index = data.get('camera_index', 0)
        
        # 카메라 전환 시도
        success = camera_manager.start_camera(camera_index)
        
        if success:
            # 현재 카메라 정보 가져오기
            current_name = get_camera_name(camera_index)
            
            return jsonify({
                'success': True,
                'message': f'카메라 {camera_index}로 전환되었습니다.',
                'camera_index': camera_index,
                'camera_name': current_name
            })
        else:
            return jsonify({
                'success': False,
                'message': f'카메라 {camera_index}를 찾을 수 없습니다.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'카메라 전환 중 오류: {str(e)}'
        })

@main_bp.route("/detect_cameras")
def detect_cameras():
    """
    사용 가능한 카메라 감지 라우트
    """
    import cv2
    
    available_cameras = []
    
    # 인덱스 0부터 5까지 테스트
    for i in range(6):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # 카메라 속성 정보 가져오기
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                # 프레임 읽기 테스트
                ret, frame = cap.read()
                
                camera_info = {
                    'index': i,
                    'name': get_camera_name(i),
                    'resolution': f'{width}x{height}',
                    'fps': fps,
                    'can_read': ret
                }
                
                available_cameras.append(camera_info)
                print(f"카메라 {i} 감지됨: {width}x{height}, FPS: {fps}, 읽기: {ret}")
                
                cap.release()
            else:
                print(f"카메라 {i} 연결 실패")
        except Exception as e:
            print(f"카메라 {i} 테스트 오류: {e}")
    
    return jsonify({
        'available_cameras': available_cameras,
        'total_count': len(available_cameras)
    })