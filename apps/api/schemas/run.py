"""
Run Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from enum import Enum


class RunStatus(str, Enum):
    """Run 상태"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RunCreate(BaseModel):
    """Run 생성 요청 스키마"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dataset_id": 1,
                "strategy_id": 1,
                "preset_id": 1
            }
        }
    )
    
    dataset_id: int = Field(..., description="데이터셋 ID")
    strategy_id: int = Field(..., description="전략 ID")
    preset_id: Optional[int] = Field(default=None, description="프리셋 ID (없으면 기본 프리셋 사용)")


class RunResponse(BaseModel):
    """Run 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    run_id: int
    dataset_id: int
    strategy_id: int
    status: RunStatus
    engine_version: str
    initial_balance: float
    preset_id: Optional[int] = Field(default=None, description="프리셋 ID")
    started_at: Optional[int]
    completed_at: Optional[int]
    run_artifacts: Optional[Dict[str, Any]]
    
    # 진행률 추적 필드
    progress_percent: Optional[float] = Field(default=None, description="진행률 (0~100)")
    processed_bars: Optional[int] = Field(default=None, description="처리된 봉 개수")
    total_bars: Optional[int] = Field(default=None, description="전체 봉 개수")


class RunList(BaseModel):
    """Run 목록 응답 스키마"""
    runs: list[RunResponse]
    total: int

