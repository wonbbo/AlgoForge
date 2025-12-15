"""
API 응답 유틸리티 함수
"""

from typing import Optional, Dict, Any


def error_response(
    message: str,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    에러 응답 생성
    
    Args:
        message: 에러 메시지
        status_code: HTTP 상태 코드
        details: 추가 상세 정보
        
    Returns:
        Dict: 에러 응답 딕셔너리
    """
    response = {
        "success": False,
        "error": {
            "message": message,
            "status_code": status_code
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return response


def success_response(
    data: Any,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    성공 응답 생성
    
    Args:
        data: 응답 데이터
        message: 추가 메시지 (선택)
        
    Returns:
        Dict: 성공 응답 딕셔너리
    """
    response = {
        "success": True,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    return response

