# ~/Desktop/autocarz(라파다운로드본)/src/routes/camera_routes.py
# 카메라 관련 Flask 라우트

from flask import Blueprint, Response, request, jsonify
from camera.camera_manager import switch_camera, get_status, find_available_camera_index, logger
import json

# 카메라 라우트 블루프린트 생성
camera_bp = Blueprint('camera', __name__)

@camera_bp.route('/video_feed')
def video_feed():
    """
    실시간 비디오 스트림 제공
    """
    logger.log("INFO", "비디오 스트림 요청 받음")
    
    try:
        from camera.camera_manager import generate_frames
        return Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.log("ERROR", "비디오 스트림 생성 중 오류", e)
        return jsonify({"error": "비디오 스트림 생성 실패"}), 500

@camera_bp.route('/switch_camera', methods=['POST'])
def switch_camera_route():
    """
    카메라 전환 API
    """
    logger.log("INFO", "카메라 전환 요청 받음")
    
    try:
        data = request.get_json()
        if not data or 'camera_index' not in data:
            logger.log("ERROR", "잘못된 요청 데이터")
            return jsonify({
                "success": False,
                "error": "camera_index가 필요합니다"
            }), 400
        
        camera_index = int(data['camera_index'])
        logger.log("INFO", f"카메라 전환 요청: 인덱스 {camera_index}")
        
        # 카메라 전환 시도
        success = switch_camera(camera_index)
        
        if success:
            logger.log("SUCCESS", f"카메라 {camera_index}로 전환 성공")
            return jsonify({
                "success": True,
                "message": f"카메라 {camera_index}로 전환되었습니다",
                "camera_index": camera_index
            })
        else:
            logger.log("ERROR", f"카메라 {camera_index} 전환 실패")
            return jsonify({
                "success": False,
                "error": f"카메라 {camera_index} 전환에 실패했습니다"
            }), 500
            
    except ValueError as e:
        logger.log("ERROR", f"잘못된 카메라 인덱스: {e}")
        return jsonify({
            "success": False,
            "error": "유효하지 않은 카메라 인덱스입니다"
        }), 400
    except Exception as e:
        logger.log("ERROR", f"카메라 전환 중 예외 발생", e)
        return jsonify({
            "success": False,
            "error": "카메라 전환 중 오류가 발생했습니다"
        }), 500

@camera_bp.route('/status')
def camera_status():
    """
    카메라 상태 정보 제공
    """
    logger.log("INFO", "카메라 상태 요청 받음")
    
    try:
        status = get_status()
        logger.log("DEBUG", f"상태 정보 반환: {status}")
        return jsonify(status)
    except Exception as e:
        logger.log("ERROR", "상태 정보 조회 중 오류", e)
        return jsonify({
            "error": "상태 정보 조회 실패",
            "camera_connected": False,
            "streaming": False
        }), 500

@camera_bp.route('/detect_cameras')
def detect_cameras():
    """
    사용 가능한 카메라 목록 제공
    """
    logger.log("INFO", "카메라 감지 요청 받음")
    
    try:
        available_cameras = find_available_camera_index()
        logger.log("INFO", f"감지된 카메라: {available_cameras}")
        
        return jsonify({
            "success": True,
            "available_cameras": available_cameras,
            "count": len(available_cameras)
        })
    except Exception as e:
        logger.log("ERROR", "카메라 감지 중 오류", e)
        return jsonify({
            "success": False,
            "error": "카메라 감지 중 오류가 발생했습니다",
            "available_cameras": []
        }), 500

@camera_bp.route('/test_camera/<int:camera_index>')
def test_camera_route(camera_index):
    """
    특정 카메라 테스트
    """
    logger.log("INFO", f"카메라 {camera_index} 테스트 요청 받음")
    
    try:
        from camera.camera_manager import test_camera
        success = test_camera(camera_index)
        
        if success:
            logger.log("SUCCESS", f"카메라 {camera_index} 테스트 성공")
            return jsonify({
                "success": True,
                "message": f"카메라 {camera_index} 테스트 성공",
                "camera_index": camera_index
            })
        else:
            logger.log("ERROR", f"카메라 {camera_index} 테스트 실패")
            return jsonify({
                "success": False,
                "error": f"카메라 {camera_index} 테스트 실패",
                "camera_index": camera_index
            }), 500
            
    except Exception as e:
        logger.log("ERROR", f"카메라 {camera_index} 테스트 중 예외 발생", e)
        return jsonify({
            "success": False,
            "error": "카메라 테스트 중 오류가 발생했습니다"
        }), 500

@camera_bp.route('/debug_log')
def get_debug_log():
    """
    디버그 로그 파일 내용 제공
    """
    logger.log("INFO", "디버그 로그 요청 받음")
    
    try:
        with open("camera_debug.log", "r", encoding="utf-8") as f:
            log_content = f.read()
        
        return jsonify({
            "success": True,
            "log_content": log_content,
            "log_file": "camera_debug.log"
        })
    except FileNotFoundError:
        logger.log("WARNING", "로그 파일이 없습니다")
        return jsonify({
            "success": False,
            "error": "로그 파일이 없습니다",
            "log_content": ""
        }), 404
    except Exception as e:
        logger.log("ERROR", "로그 파일 읽기 중 오류", e)
        return jsonify({
            "success": False,
            "error": "로그 파일 읽기 실패"
        }), 500

@camera_bp.route('/clear_log')
def clear_debug_log():
    """
    디버그 로그 파일 초기화
    """
    logger.log("INFO", "로그 파일 초기화 요청 받음")
    
    try:
        with open("camera_debug.log", "w", encoding="utf-8") as f:
            f.write("")
        
        logger.log("INFO", "로그 파일 초기화 완료")
        return jsonify({
            "success": True,
            "message": "로그 파일이 초기화되었습니다"
        })
    except Exception as e:
        logger.log("ERROR", "로그 파일 초기화 중 오류", e)
        return jsonify({
            "success": False,
            "error": "로그 파일 초기화 실패"
        }), 500 