"""
Trade Schemas
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional


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
    is_closed: bool
    total_pnl: Optional[float]
    legs: list[TradeLegResponse] = []


class TradeList(BaseModel):
    """Trade 목록 응답 스키마"""
    trades: list[TradeResponse]
    total: int

