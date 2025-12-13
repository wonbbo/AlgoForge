"""
Indicator Schemas - 지표 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


class IndicatorBase(BaseModel):
    """지표 기본 스키마"""
    name: str = Field(..., description="지표 이름 (예: 'EMA', 'MACD')")
    type: str = Field(..., description="지표 타입 (고유 ID, 예: 'ema', 'macd')")
    description: Optional[str] = Field(None, description="지표 설명")
    category: str = Field(
        ..., 
        description="카테고리: 'trend', 'momentum', 'volatility', 'volume' 중 하나"
    )


class IndicatorResponse(IndicatorBase):
    """지표 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    indicator_id: int = Field(..., description="지표 ID")
    implementation_type: str = Field(
        ..., 
        description="구현 타입: 'builtin' (내장) 또는 'custom' (커스텀)"
    )
    code: Optional[str] = Field(
        None,
        description="Python 함수 코드 (커스텀 지표인 경우만 포함)"
    )
    params_schema: Optional[str] = Field(
        None, 
        description="파라미터 스키마 (JSON 문자열)"
    )
    output_fields: List[str] = Field(
        ..., 
        description="출력 필드명 목록 (예: ['main'] 또는 ['main', 'signal', 'histogram'])"
    )
    created_at: int = Field(..., description="생성 시간 (Unix timestamp)")


class CustomIndicatorCreate(IndicatorBase):
    """커스텀 지표 생성 요청 스키마"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Custom MACD",
                "type": "custom_macd",
                "description": "커스텀 MACD 지표",
                "category": "momentum",
                "code": """def calculate_custom_macd(df, params):
    from ta.trend import MACD
    fast = params.get('fast_period', 12)
    slow = params.get('slow_period', 26)
    signal = params.get('signal_period', 9)
    
    macd = MACD(df['close'], slow, fast, signal, fillna=True)
    return {
        'main': macd.macd(),
        'signal': macd.macd_signal(),
        'histogram': macd.macd_diff()
    }""",
                "params_schema": '{"fast_period": 12, "slow_period": 26, "signal_period": 9}',
                "output_fields": ["main", "signal", "histogram"]
            }
        }
    )
    
    code: str = Field(
        ..., 
        description="Python 함수 코드 (함수명은 자유, df와 params 두 인자를 받아야 함)"
    )
    params_schema: str = Field(
        ..., 
        description="파라미터 스키마 (JSON 문자열, 기본값 포함)"
    )
    output_fields: List[str] = Field(
        ..., 
        description="출력 필드명 목록 (예: ['main'] 또는 ['main', 'signal', 'histogram'])"
    )


class CustomIndicatorUpdate(BaseModel):
    """커스텀 지표 수정 요청 스키마"""
    name: Optional[str] = Field(None, description="지표 이름")
    description: Optional[str] = Field(None, description="지표 설명")
    category: Optional[str] = Field(None, description="카테고리: trend/momentum/volatility/volume")
    code: Optional[str] = Field(None, description="Python 함수 코드")
    params_schema: Optional[str] = Field(None, description="파라미터 스키마")
    output_fields: Optional[List[str]] = Field(None, description="출력 필드명 목록")


class IndicatorList(BaseModel):
    """지표 목록 응답 스키마"""
    indicators: List[IndicatorResponse] = Field(..., description="지표 목록")
    total: int = Field(..., description="전체 지표 개수")


class IndicatorValidationResult(BaseModel):
    """지표 코드 검증 결과 스키마"""
    is_valid: bool = Field(..., description="검증 통과 여부")
    message: str = Field(..., description="검증 결과 메시지")
    errors: Optional[List[str]] = Field(None, description="에러 목록 (검증 실패 시)")


class CodeValidationRequest(BaseModel):
    """코드 검증 요청 스키마"""
    code: str = Field(..., description="검증할 Python 함수 코드")

