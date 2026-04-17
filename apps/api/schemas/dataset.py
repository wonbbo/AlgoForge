"""
Dataset Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal


MarketType = Literal["spot", "futures_um"]


class DatasetCreate(BaseModel):
    """데이터셋 생성 요청 스키마"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "XRPUSDT 2024 5m",
                "description": "XRPUSDT 2024년 5분봉",
                "timeframe": "5m",
                "symbol": "XRPUSDT",
                "market_type": "futures_um"
            }
        }
    )

    name: str = Field(..., description="데이터셋 이름")
    description: Optional[str] = Field(None, description="데이터셋 설명")
    timeframe: str = Field(default="5m", description="타임프레임 (기본값: 5m)")
    symbol: str = Field(default="XRPUSDT", description="종목 심볼")
    market_type: MarketType = Field(default="futures_um", description="시장 타입")


class BinanceFetchRequest(BaseModel):
    """바이낸스 자동 수집 요청 스키마"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "XRPUSDT",
                "market_type": "futures_um",
                "timeframe": "5m",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "name": "XRPUSDT 2024 5m"
            }
        }
    )

    symbol: str = Field(default="XRPUSDT", description="종목 심볼")
    market_type: MarketType = Field(default="futures_um", description="시장 타입")
    timeframe: str = Field(default="5m", description="타임프레임 (1m, 5m, 15m, 1h, 4h, 1d 등)")
    start_date: str = Field(..., description="시작 날짜 'YYYY-MM-DD' (UTC)")
    end_date: str = Field(..., description="종료 날짜 'YYYY-MM-DD' (UTC, 포함)")
    name: Optional[str] = Field(None, description="데이터셋 이름 (미지정 시 자동 생성)")
    description: Optional[str] = Field(None, description="설명")


class DatasetResponse(BaseModel):
    """데이터셋 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)

    dataset_id: int
    name: str
    description: Optional[str]
    symbol: str = "XRPUSDT"
    market_type: str = "futures_um"
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

