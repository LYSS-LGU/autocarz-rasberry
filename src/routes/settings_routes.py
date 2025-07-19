# /home/pi/autocarz/src/routes/settings_routes.py
# 카메라/AI 설정 변경 라우트 담당
# 프론트엔드에서 설정 변경 요청을 받아 처리

from flask import Blueprint, request, jsonify
from utils.settings_manager import save_flip_settings, save_detection_settings

settings_bp = Blueprint('settings', __name__)

@settings_bp.route("/update_settings", methods=["POST"])
def update_settings():
    """
    카메라 반전/회전 등 설정 변경 라우트
    - 프론트엔드에서 JSON으로 설정값 전달
    - 성공/실패 여부와 메시지 반환
    """
    try:
        data = request.get_json()
        result = save_flip_settings(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"카메라 설정 적용 실패: {str(e)}"})

@settings_bp.route("/update_detection_settings", methods=["POST"])
def update_detection_settings():
    """
    AI(객체 인식) 관련 설정 변경 라우트
    - 프론트엔드에서 JSON으로 설정값 전달
    - 성공/실패 여부와 메시지 반환
    """
    try:
        data = request.get_json()
        result = save_detection_settings(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"검출 설정 적용 실패: {str(e)}"}) 