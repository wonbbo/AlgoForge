"""
Strategy Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any


class StrategyCreate(BaseModel):
    """전략 생성 요청 스키마"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "EMA Cross Strategy",
                "description": "EMA 교차 전략",
                "definition": {
                    "entry_long": {"indicator": "ema_cross", "params": {"fast": 12, "slow": 26}},
                    "entry_short": {"indicator": "ema_cross_down", "params": {"fast": 12, "slow": 26}}
                }
            }
        }
    )
    
    name: str = Field(..., description="전략 이름")
    description: Optional[str] = Field(None, description="전략 설명")
    definition: Dict[str, Any] = Field(..., description="전략 정의 (JSON)")


class StrategyResponse(BaseModel):
    """전략 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    strategy_id: int
    name: str
    description: Optional[str]
    strategy_hash: str
    definition: Dict[str, Any]
    created_at: int


class StrategyList(BaseModel):
    """전략 목록 응답 스키마"""
    strategies: list[StrategyResponse]
    total: int

