"""
거래 구간(Trade Leg) 모델
"""
from dataclasses import dataclass
from typing import Literal


ExitType = Literal['SL', 'TP1', 'BE', 'REVERSE']


@dataclass
class TradeLeg:
    """
    거래 구간(Trade Leg) 모델
    
    하나의 trade는 최대 2개의 leg를 가짐:
    - TP1 leg (qty_ratio=0.5) - 50% 부분 청산
    - FINAL leg (잔여 수량) - SL/BE/REVERSE로 최종 종료
    
    Attributes:
        trade_id: 거래 ID
        exit_type: 청산 타입 ('SL', 'TP1', 'BE', 'REVERSE')
        exit_timestamp: 청산 시각 (UNIX timestamp)
        exit_price: 청산 가격
        qty_ratio: 수량 비율 (0~1 사이, 0.5 = 50%)
        pnl: 손익 (포지션 크기 반영된 최종 PnL)
    """
    trade_id: int
    exit_type: ExitType
    exit_timestamp: int
    exit_price: float
    qty_ratio: float
    pnl: float
    
    def __post_init__(self):
        """데이터 검증"""
        # trade_id는 양수여야 함
        if self.trade_id <= 0:
            raise ValueError("trade_id는 양수여야 합니다")
        
        # exit_timestamp는 양수여야 함
        if self.exit_timestamp < 0:
            raise ValueError("exit_timestamp는 0 이상이어야 합니다")
        
        # exit_price는 양수여야 함
        if self.exit_price <= 0:
            raise ValueError("exit_price는 양수여야 합니다")
        
        # qty_ratio는 0~1 사이여야 함
        if not (0 < self.qty_ratio <= 1):
            raise ValueError("qty_ratio는 0 초과 1 이하여야 합니다")

