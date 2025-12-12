"""
Metrics Schemas
"""

from pydantic import BaseModel, ConfigDict


class MetricsResponse(BaseModel):
    """Metrics 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    metric_id: int
    run_id: int
    trades_count: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    tp1_hit_rate: float
    be_exit_rate: float
    total_pnl: float
    average_pnl: float
    profit_factor: float
    max_drawdown: float
    score: float
    grade: str

