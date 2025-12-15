"""
Dataset Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class DatasetCreate(BaseModel):
    """데이터셋 생성 요청 스키마"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "BTC 2024-01 Dataset",
                "description": "BTC 2024년 1월 데이터",
                "timeframe": "5m"
            }
        }
    )
    
    name: str = Field(..., description="데이터셋 이름")
    description: Optional[str] = Field(None, description="데이터셋 설명")
    timeframe: str = Field(default="5m", description="타임프레임 (기본값: 5m)")


class DatasetResponse(BaseModel):
    """데이터셋 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    dataset_id: int
    name: str
    description: Optional[str]
    timeframe: str
    dataset_hash: str
    file_path: str
    bars_count: int
    start_timestamp: int
    end_timestamp: int
    created_at: int


class DatasetList(BaseModel):
    """데이터셋 목록 응답 스키마"""
    datasets: list[DatasetResponse]
    total: int

