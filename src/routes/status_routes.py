# /home/pi/autocarz/src/routes/status_routes.py
# 시스템 상태 확인 라우트 담당
# 현재 카메라/AI/설정 등 시스템 상태를 JSON으로 반환

from flask import Blueprint, jsonify
from camera.camera_manager import camera_manager
import platform
from datetime import datetime

status_bp = Blueprint('status', __name__)

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
        "available_cameras": []  # 간단하게 빈 배열로 설정
    }
    
    return status

@status_bp.route("/status")
def status():
    """
    시스템 상태 반환 라우트
    - 카메라 연결 상태 등 get_status() 결과를 JSON으로 반환
    """
    return jsonify(get_status()) 