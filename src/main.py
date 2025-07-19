# ~/Desktop/autocarz(라파다운로드본)/src/main.py
# [수정] USB 카메라만 확인하고 서버를 시작하는 버전

import os
import sys
import cv2
import platform
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from camera.camera_manager import camera_manager

# --- USB 카메라 정보 ---
USB_CAMERA_INDEX = 1
USB_CAMERA_NAME = "SC-FD110B PC Camera"

# 프로젝트 루트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# 간단한 로거 클래스
class SimpleLogger:
    def log(self, level, message, error=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")
        if error:
            print(f"[{timestamp}] [{level}] 에러: {error}")

logger = SimpleLogger()

def check_specific_camera(index, name=None):
    """
    지정한 인덱스의 카메라 연결 상태만 명확하게 확인하고 결과를 출력합니다.
    """
    print(f"👀 [{name}] (인덱스 {index}) 연결 확인을 시작합니다...")
    
    try:
        # 기존 카메라가 실행 중이면 먼저 정지
        if camera_manager.is_running:
            print(f"    ⏳ 기존 카메라 정지 중...")
            camera_manager.stop_camera()
            time.sleep(2.0)
        
        # cv2.CAP_DSHOW는 윈도우에서 카메라를 더 안정적으로 불러오는 옵션입니다.
        if platform.system().lower() == "windows":
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(index)
        
        if cap and cap.isOpened():
            # 카메라 설정
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # 프레임 읽기 테스트 (여러 번 시도)
            success_count = 0
            for i in range(3):
                ret, frame = cap.read()
                if ret and frame is not None:
                    success_count += 1
                    print(f"    ✅ 테스트 프레임 {i+1} 성공: {frame.shape}")
                else:
                    print(f"    ⚠️ 테스트 프레임 {i+1} 실패")
                time.sleep(0.5)
            
            cap.release()  # 확인 후에는 반드시 카메라를 해제해줘야 합니다.
            time.sleep(1.0)  # 해제 후 대기
            
            if success_count >= 2:
                print(f"    ✅ [연결 성공] {name}이(가) 정상적으로 인식되었습니다. (성공률: {success_count}/3)")
                return True
            else:
                print(f"    ❌ [연결 실패] {name}에서 프레임을 읽을 수 없습니다. (성공률: {success_count}/3)")
                return False
        else:
            print(f"    ❌ [연결 실패] {name}을(를) 찾을 수 없습니다. 연결 상태를 확인해주세요.")
            return False
            
    except Exception as e:
        print(f"    ❌ [연결 실패] {name} 확인 중 오류가 발생했습니다: {e}")
        return False

def find_available_camera_index():
    """
    사용 가능한 카메라 인덱스 자동 탐색
    """
    logger.log("INFO", "사용 가능한 카메라 탐색 시작")
    available_cameras = []
    
    for i in range(10):
        try:
            logger.log("DEBUG", f"카메라 {i} 테스트 중...")
            
            if platform.system().lower() == "windows":
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(i)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    available_cameras.append(i)
                    logger.log("INFO", f"카메라 {i} 발견: {frame.shape}")
                else:
                    logger.log("WARNING", f"카메라 {i} 연결됨 but 프레임 읽기 실패")
                cap.release()
            else:
                logger.log("DEBUG", f"카메라 {i} 연결 실패")
            
            time.sleep(0.1)
            
        except Exception as e:
            logger.log("ERROR", f"카메라 {i} 테스트 중 예외 발생", e)
    
    logger.log("INFO", f"카메라 탐색 완료: {available_cameras}")
    return available_cameras

def get_status():
    """
    카메라 상태 정보 반환
    """
    status = {
        "camera_connected": camera_manager.is_running and camera_manager.cap is not None,
        "streaming": camera_manager.is_running,
        "camera_index": camera_manager.camera_index,
        "os_type": platform.system().lower(),
        "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "available_cameras": find_available_camera_index()
    }
    
    logger.log("DEBUG", f"상태 정보: {status}")
    return status

def switch_camera(camera_index):
    """
    카메라 전환
    """
    logger.log("INFO", f"카메라 전환 시작: {camera_manager.camera_index} -> {camera_index}")
    
    try:
        # 현재 카메라 정지
        if camera_manager.is_running:
            logger.log("DEBUG", "현재 카메라 정지 중...")
            camera_manager.stop_camera()
            time.sleep(3.0)
        
        # 새 카메라 시작
        if camera_manager.start_camera(camera_index):
            logger.log("SUCCESS", f"카메라 {camera_index}로 전환 성공")
            time.sleep(3)
            return True
        else:
            logger.log("ERROR", f"카메라 {camera_index} 시작 실패")
            return False
            
    except Exception as e:
        logger.log("ERROR", f"카메라 전환 중 예외 발생", e)
        return False

def create_app():
    """Flask 앱을 생성하고 블루프린트를 등록하는 함수"""
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )
    
    # 디버그 모드 활성화
    app.config['DEBUG'] = True
    
    logger.log("INFO", f"Flask 앱 초기화: 템플릿 폴더={app.template_folder}")
    logger.log("INFO", f"Flask 앱 초기화: 정적 폴더={app.static_folder}")

    # 블루프린트들을 앱에 등록합니다.
    try:
        from routes.camera_routes import camera_bp
        app.register_blueprint(camera_bp)
        logger.log("SUCCESS", "카메라 라우트 블루프린트 등록 완료")
    except Exception as e:
        logger.log("ERROR", "카메라 라우트 블루프린트 등록 실패", e)

    try:
        from routes.main_routes import main_bp
        app.register_blueprint(main_bp)
        logger.log("SUCCESS", "메인 라우트 블루프린트 등록 완료")
    except Exception as e:
        logger.log("ERROR", "메인 라우트 블루프린트 등록 실패", e)

    try:
        from routes.status_routes import status_bp
        app.register_blueprint(status_bp)
        logger.log("SUCCESS", "상태 라우트 블루프린트 등록 완료")
    except Exception as e:
        logger.log("ERROR", "상태 라우트 블루프린트 등록 실패", e)

    try:
        from routes.settings_routes import settings_bp
        app.register_blueprint(settings_bp)
        logger.log("SUCCESS", "설정 라우트 블루프린트 등록 완료")
    except Exception as e:
        logger.log("ERROR", "설정 라우트 블루프린트 등록 실패", e)

    @app.route('/')
    def index():
        """
        메인 페이지
        """
        logger.log("INFO", "메인 페이지 요청 받음")
        
        try:
            # 템플릿 파일 존재 확인
            template_path = os.path.join(app.template_folder or '', 'yolo_opencv.html')
            if not os.path.exists(template_path):
                logger.log("ERROR", f"템플릿 파일이 없습니다: {template_path}")
                return jsonify({"error": "템플릿 파일을 찾을 수 없습니다"}), 500
            
            logger.log("INFO", f"템플릿 파일 확인됨: {template_path}")
            
            # 시스템 정보 수집
            system_info = {
                "os": os.name,
                "platform": sys.platform,
                "python_version": sys.version
            }
            
            # 카메라 상태 정보
            camera_status = get_status()
            
            # 사용 가능한 카메라 목록
            available_cameras = find_available_camera_index()
            
            # 템플릿에 전달할 컨텍스트
            context = {
                "system_info": system_info,
                "camera_status": camera_status,
                "available_cameras": available_cameras,
                "yolo_status": "Ready",
                "opencv_status": "Ready",
                "camera_info": {
                    "name": f"Camera {camera_status.get('camera_index', 0)}",
                    "index": camera_status.get('camera_index', 0)
                },
                "detection_settings": {
                    "yolo_enabled": True,
                    "opencv_enabled": True,
                    "show_fps": True,
                    "quality": 85,
                    "fps_limit": 30,
                    "resolution": "1280x720"
                },
                "flip_settings": {
                    "horizontal": False,
                    "vertical": False,
                    "rotation": 0
                },
                "color_correction_settings": {
                    "enabled": False,
                    "red_reduction": 1.0,
                    "green_boost": 1.0,
                    "blue_boost": 1.0,
                    "mode": "standard"
                }
            }
            
            logger.log("INFO", "메인 페이지 렌더링 완료")
            return render_template('yolo_opencv.html', **context)
            
        except Exception as e:
            logger.log("ERROR", "메인 페이지 렌더링 중 오류", e)
            return jsonify({"error": "페이지 로드 실패"}), 500

    @app.route('/health')
    def health_check():
        """
        헬스 체크 엔드포인트
        """
        try:
            status = get_status()
            return jsonify({
                "status": "healthy",
                "camera_connected": status.get("camera_connected", False),
                "streaming": status.get("streaming", False),
                "timestamp": status.get("last_checked", "")
            })
        except Exception as e:
            logger.log("ERROR", "헬스 체크 중 오류", e)
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 500

    @app.route('/api/system_info')
    def system_info():
        """
        시스템 정보 API
        """
        logger.log("INFO", "시스템 정보 요청 받음")
        
        try:
            import platform
            
            info = {
                "os": platform.system(),
                "os_version": platform.release(),
                "architecture": platform.architecture()[0],
                "python_version": sys.version,
                "opencv_version": "Unknown",
                "template_folder": app.template_folder or "None",
                "static_folder": app.static_folder or "None"
            }
            
            # OpenCV 버전 확인
            try:
                import cv2
                info["opencv_version"] = cv2.__version__
            except:
                pass
            
            logger.log("DEBUG", f"시스템 정보: {info}")
            return jsonify(info)
            
        except Exception as e:
            logger.log("ERROR", "시스템 정보 조회 중 오류", e)
            return jsonify({"error": "시스템 정보 조회 실패"}), 500

    @app.errorhandler(404)
    def not_found(error):
        """
        404 에러 핸들러
        """
        logger.log("WARNING", f"404 에러: {request.url}")
        return jsonify({"error": "페이지를 찾을 수 없습니다"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """
        500 에러 핸들러
        """
        logger.log("ERROR", f"500 에러: {error}")
        return jsonify({"error": "서버 내부 오류가 발생했습니다"}), 500

    print("✅ 모든 라우트(API 주소)가 성공적으로 등록되었습니다.")
    return app

if __name__ == "__main__":
    print("="*40)
    print("AutocarZ 서버 시작 프로세스")
    print("="*40)

    # 1. [핵심] 지정된 USB 카메라 연결 상태만 확인합니다.
    is_connected = check_specific_camera(index=USB_CAMERA_INDEX, name=USB_CAMERA_NAME)

    # 2. 연결 상태에 따라 다음 동작을 결정합니다.
    if is_connected:
        print("\n🚀 메인 카메라 연결 확인! 서버를 시작합니다.\n")
        
        # Flask 앱 생성
        app = create_app()
        
        # 기본 카메라를 USB 캠(1번)으로 설정하고 시작합니다.
        switch_camera(USB_CAMERA_INDEX)
        
        # [수정] use_reloader=False 옵션으로 불필요한 재시작 방지
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

    else:
        print("\n🛑 메인 카메라가 연결되지 않아 서버를 시작할 수 없습니다.")
        print("   USB 포트를 확인하거나 다른 카메라를 연결해주세요.")