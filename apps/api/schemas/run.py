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


class RunCreate(BaseModel):
    """Run 생성 요청 스키마"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dataset_id": 1,
                "strategy_id": 1,
                "initial_balance": 10000.0
            }
        }
    )
    
    dataset_id: int = Field(..., description="데이터셋 ID")
    strategy_id: int = Field(..., description="전략 ID")
    initial_balance: float = Field(default=10000.0, description="초기 자산 (기본값: 10000)")


class RunResponse(BaseModel):
    """Run 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    run_id: int
    dataset_id: int
    strategy_id: int
    status: RunStatus
    engine_version: str
    initial_balance: float
    started_at: Optional[int]
    completed_at: Optional[int]
    run_artifacts: Optional[Dict[str, Any]]


class RunList(BaseModel):
    """Run 목록 응답 스키마"""
    runs: list[RunResponse]
    total: int

