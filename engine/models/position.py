"""
포지션 모델
"""
from dataclasses import dataclass
from typing import Literal


Direction = Literal['LONG', 'SHORT']


@dataclass
class Position:
    """
    포지션 모델
    
    현재 보유 중인 포지션을 나타냄
    AlgoForge는 동시에 하나의 포지션만 보유 가능
    
    Attributes:
        trade_id: 거래 ID
        direction: 포지션 방향 (LONG/SHORT)
        entry_price: 진입 가격
        entry_timestamp: 진입 시각 (UNIX timestamp)
        position_size: 포지션 크기 (계약 수)
        stop_loss: 손절가
        take_profit_1: 1차 익절가
        initial_risk: 초기 리스크 (|entry_price - stop_loss|)
        tp1_hit: TP1 도달 여부
        tp1_occurred_this_bar: 현재 봉에서 TP1 발생 여부
            (TP1 발생 봉에서는 reverse 신호 평가를 스킵하기 위한 플래그)
    """
    trade_id: int
    direction: Direction
    entry_price: float
    entry_timestamp: int
    position_size: float
    stop_loss: float
    take_profit_1: float
    initial_risk: float
    tp1_hit: bool = False
    tp1_occurred_this_bar: bool = False
    
    def __post_init__(self):
        """데이터 검증"""
        # trade_id는 양수여야 함
        if self.trade_id <= 0:
            raise ValueError("trade_id는 양수여야 합니다")
        
        # entry_timestamp는 양수여야 함
        if self.entry_timestamp < 0:
            raise ValueError("entry_timestamp는 0 이상이어야 합니다")
        
        # 가격들은 양수여야 함
        if self.entry_price <= 0:
            raise ValueError("entry_price는 양수여야 합니다")
        if self.stop_loss <= 0:
            raise ValueError("stop_loss는 양수여야 합니다")
        if self.take_profit_1 <= 0:
            raise ValueError("take_profit_1은 양수여야 합니다")
        
        # position_size는 양수여야 함
        if self.position_size <= 0:
            raise ValueError("position_size는 양수여야 합니다")
        
        # initial_risk는 0 이상이어야 함
        if self.initial_risk < 0:
            raise ValueError("initial_risk는 0 이상이어야 합니다")
        
        # LONG 포지션의 경우: SL < entry < TP1
        if self.direction == 'LONG':
            if self.stop_loss >= self.entry_price:
                raise ValueError("LONG 포지션: stop_loss는 entry_price보다 작아야 합니다")
            if self.take_profit_1 <= self.entry_price:
                raise ValueError("LONG 포지션: take_profit_1은 entry_price보다 커야 합니다")
        
        # SHORT 포지션의 경우: TP1 < entry < SL
        if self.direction == 'SHORT':
            if self.stop_loss <= self.entry_price:
                raise ValueError("SHORT 포지션: stop_loss는 entry_price보다 커야 합니다")
            if self.take_profit_1 >= self.entry_price:
                raise ValueError("SHORT 포지션: take_profit_1은 entry_price보다 작아야 합니다")

