# /home/pi/autocarz/src/utils/settings_manager.py
# 설정 파일 로드/저장, flip/detection 세팅 관리 담당
# 실제 구현 필요(TODO) 부분 명확히 표시

def save_flip_settings(data):
    """
    카메라 flip(반전/회전) 설정을 저장하는 함수
    data: 프론트엔드에서 전달된 설정값(dict)
    return: 저장 성공/실패 여부와 메시지(dict)
    TODO: 실제 파일 저장/적용 로직 구현 필요
    """
    return {"success": True, "message": "설정 저장(임시)"}

def save_detection_settings(data):
    """
    AI(객체 인식) 관련 설정을 저장하는 함수
    data: 프론트엔드에서 전달된 설정값(dict)
    return: 저장 성공/실패 여부와 메시지(dict)
    TODO: 실제 파일 저장/적용 로직 구현 필요
    """
    return {"success": True, "message": "설정 저장(임시)"} 