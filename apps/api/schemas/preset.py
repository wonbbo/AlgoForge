"""
Preset Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class PresetBase(BaseModel):
    """프리셋 기본 스키마"""
    name: str = Field(..., description="프리셋 이름")
    description: Optional[str] = Field(None, description="설명")
    initial_balance: float = Field(1000.0, ge=0, description="초기 자산 (USDT)")
    risk_percent: float = Field(0.02, gt=0, le=1, description="거래당 최대 손실 비율 (0.02 = 2%)")
    risk_reward_ratio: float = Field(1.5, gt=0, description="리스크 대비 보상 비율")
    rebalance_interval: int = Field(50, ge=1, description="잔고 재평가 주기 (거래 단위)")


class PresetCreate(PresetBase):
    """프리셋 생성 요청 스키마"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "공격적",
                "description": "높은 리스크, 높은 수익 목표",
                "initial_balance": 1000.0,
                "risk_percent": 0.03,
                "risk_reward_ratio": 1.5,
                "rebalance_interval": 50
            }
        }
    )


class PresetUpdate(BaseModel):
    """프리셋 수정 요청 스키마"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "공격적 (수정)",
                "description": "높은 리스크, 높은 수익 목표",
                "risk_percent": 0.04
            }
        }
    )
    
    name: Optional[str] = Field(None, description="프리셋 이름")
    description: Optional[str] = Field(None, description="설명")
    initial_balance: Optional[float] = Field(None, ge=0, description="초기 자산")
    risk_percent: Optional[float] = Field(None, gt=0, le=1, description="리스크 비율")
    risk_reward_ratio: Optional[float] = Field(None, gt=0, description="리스크 보상 비율")
    rebalance_interval: Optional[int] = Field(None, ge=1, description="재평가 주기")
    is_default: Optional[bool] = Field(None, description="기본 프리셋 여부")


class PresetResponse(PresetBase):
    """프리셋 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    preset_id: int
    is_default: bool
    created_at: int
    updated_at: int


class PresetList(BaseModel):
    """프리셋 목록 응답 스키마"""
    presets: list[PresetResponse]
    total: int
