"""
Trade Schemas
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, List, Any


class TradeLegResponse(BaseModel):
    """TradeLeg 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    leg_id: int
    trade_id: int
    exit_type: str  # 'SL', 'TP1', 'BE', 'REVERSE'
    exit_timestamp: int
    exit_price: float
    qty_ratio: float
    pnl: float


class TradeResponse(BaseModel):
    """Trade 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    trade_id: int
    run_id: int
    direction: str  # 'LONG', 'SHORT'
    entry_timestamp: int
    entry_price: float
    position_size: float
    initial_risk: float
    stop_loss: float
    take_profit_1: float
    balance_at_entry: Optional[float] = None  # 진입 시점의 잔고
    leverage: float = 1.0  # 사용한 레버리지 (기본값 1.0)
    is_closed: bool
    total_pnl: Optional[float]
    legs: list[TradeLegResponse] = []


class TradeList(BaseModel):
    """Trade 목록 응답 스키마"""
    trades: list[TradeResponse]
    total: int


class BarData(BaseModel):
    """봉 데이터 스키마 (차트용)"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class ChartDataResponse(BaseModel):
    """차트 데이터 응답 스키마"""
    bars: List[BarData]
    indicators: Dict[str, List[float]]  # indicator_id -> 값 배열
    indicator_types: Dict[str, str]  # indicator_id -> "overlay" | "oscillator"
    trade_info: Dict[str, Any]  # 거래 정보 (진입/청산 시점 등)

