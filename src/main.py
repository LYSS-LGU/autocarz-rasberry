# ~/autocarz/src/main.py
# [개선] 카메라 탐색을 한 번만 수행하여 자원 충돌 가능성을 줄인 코드

import os
import sys
import cv2
import platform
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
# camera_manager는 별도의 파일에 정의되어 있다고 가정합니다.
from camera.camera_manager import camera_manager

# --- 카메라 정보 ---
USB_CAMERA_NAME = "SC-FD110B PC Camera"

# --- 경로 설정 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# --- 로거 클래스 ---
class SimpleLogger:
    def log(self, level, message, error=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")
        if error:
            print(f"[{timestamp}] [{level}] 에러: {error}")

logger = SimpleLogger()


# --- 카메라 제어 함수들 ---

def find_available_camera_indices():
    """시스템에 연결된 모든 사용 가능한 카메라의 인덱스 목록을 찾는 함수"""
    logger.log("INFO", "사용 가능한 카메라 탐색 시작...")
    available_indices = []
    for i in range(10):
        try:
            if platform.system().lower() == "windows":
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(i)
            
            if cap.isOpened():
                available_indices.append(i)
                cap.release()
        except Exception:
            continue
    
    logger.log("INFO", f"사용 가능한 카메라 인덱스 목록: {available_indices}")
    return available_indices

def start_camera_streaming(camera_index):
    """지정된 인덱스의 카메라로 스트리밍을 '시작'하고 성공 여부를 반환하는 함수."""
    logger.log("INFO", f"카메라 스트리밍 시작 시도 (대상 인덱스: {camera_index})")
    try:
        if camera_manager.start_camera(camera_index):
            logger.log("SUCCESS", f"✅ 카메라 {camera_index} 스트리밍 시작 성공!")
            time.sleep(2) # 카메라 안정화 시간
            return True
        else:
            logger.log("ERROR", f"❌ 카메라 {camera_index} 스트리밍 시작 실패.")
            return False
    except Exception as e:
        logger.log("ERROR", f"카메라 시작 중 예외 발생", e)
        return False

# --- Flask 앱 설정 ---

# [수정] create_app 함수가 카메라 목록을 인자로 받도록 변경
def create_app(available_cameras):
    """Flask 앱을 생성하고 라우트를 설정하는 함수"""
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )
    app.config['DEBUG'] = True
    
    @app.route('/')
    def index():
        """메인 페이지를 렌더링하고, 필요한 모든 데이터를 HTML로 전달합니다."""
        logger.log("INFO", "메인 페이지 요청 받음")
        
        current_camera_index = camera_manager.camera_index if camera_manager.camera_index is not None else "N/A"
        
        context = {
            "camera_info": { "name": f"Camera {current_camera_index}", "index": current_camera_index },
            "detection_settings": { "resolution": "1280x720", "yolo_enabled": True, "opencv_enabled": True, "show_fps": True, "quality": 85, "fps_limit": 30 },
            "flip_settings": { "horizontal": False, "vertical": False, "rotation": 0 },
            "color_correction_settings": { "enabled": False, "red_reduction": 1.0, "green_boost": 1.0, "blue_boost": 1.0, "mode": "standard" },
            "available_cameras": available_cameras, # [수정] 인자로 받은 카메라 목록을 사용
            "yolo_status": "준비됨",
            "opencv_status": "준비됨"
        }
        
        return render_template('yolo_opencv.html', **context)

    @app.route('/video_feed')
    def video_feed():
        """비디오 스트림을 제공하는 엔드포인트"""
        return Response(camera_manager.generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/get_current_camera')
    def get_current_camera():
        """현재 카메라 정보를 반환하는 API"""
        current_camera_index = camera_manager.camera_index if camera_manager.camera_index is not None else -1
        return jsonify({
            "camera_index": current_camera_index,
            "camera_name": f"Camera {current_camera_index}",
            "is_running": camera_manager.is_running,
            "available_cameras": available_cameras
        })

    @app.route('/switch_camera', methods=['POST'])
    def switch_camera():
        """카메라를 전환하는 API"""
        try:
            data = request.get_json()
            new_camera_index = data.get('camera_index', 0)
            
            logger.log("INFO", f"카메라 전환 요청: {new_camera_index}")
            
            if new_camera_index in available_cameras:
                if camera_manager.start_camera(new_camera_index):
                    return jsonify({
                        "success": True,
                        "message": f"카메라 {new_camera_index}로 전환 성공",
                        "camera_index": new_camera_index
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": f"카메라 {new_camera_index} 시작 실패"
                    }), 500
            else:
                return jsonify({
                    "success": False,
                    "message": f"카메라 {new_camera_index}를 찾을 수 없습니다"
                }), 404
        except Exception as e:
            logger.log("ERROR", f"카메라 전환 중 오류 발생", e)
            return jsonify({
                "success": False,
                "message": f"카메라 전환 중 오류: {str(e)}"
            }), 500

    @app.route('/favicon.ico')
    def favicon():
        """파비콘 요청 처리"""
        return '', 204  # No content

    print("✅ 모든 라우트(API 주소)가 성공적으로 등록되었습니다.")
    return app


# --- 프로그램 메인 실행부 ---

if __name__ == "__main__":
    print("="*40)
    print("AutocarZ 서버 시작 프로세스")
    print("="*40)

    # [수정] 카메라 목록을 맨 처음에 딱 한 번만 찾아서 변수에 저장합니다.
    available_indices = find_available_camera_indices()
    target_camera_index = -1

    if not available_indices:
        print("\n🛑 연결된 카메라를 찾을 수 없습니다. USB 포트를 확인해주세요.")
        sys.exit()
    elif len(available_indices) == 1:
        target_camera_index = available_indices[0]
        print(f"✅ 단일 카메라(인덱스 {target_camera_index})를 발견했습니다. 이 카메라를 사용합니다.")
    else:
        target_camera_index = available_indices[-1]
        print(f"✅ 여러 카메라({available_indices})를 발견했습니다.")
        print(f"   ➡️ 외부 USB 웹캠으로 추정되는 마지막 인덱스({target_camera_index})의 카메라를 사용합니다.")

    if start_camera_streaming(target_camera_index):
        print("\n🚀 메인 카메라 연결 및 실행 성공! 서버를 시작합니다.\n")
        # [수정] 찾은 카메라 목록을 create_app 함수에 전달합니다.
        app = create_app(available_indices)
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    else:
        print(f"\n🛑 카메라(인덱스 {target_camera_index})를 실행할 수 없어 서버를 시작하지 못했습니다.")
        print("   프로그램을 종료합니다. USB 연결을 확인하고 다시 시도해주세요.")
