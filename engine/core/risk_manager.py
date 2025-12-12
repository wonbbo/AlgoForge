"""
리스크 관리 모듈
"""
from typing import Tuple
from ..models.position import Position, Direction


class RiskManager:
    """
    리스크 관리 클래스
    
    포지션 크기 계산, TP1 가격 계산, SL→BE 이동 등의
    리스크 관리 기능을 제공
    """
    
    def __init__(
        self, 
        initial_balance: float, 
        risk_percent: float = 0.02,
        risk_reward_ratio: float = 1.5
    ):
        """
        Args:
            initial_balance: 초기 자산
            risk_percent: 1 트레이드 최대 손실 비율 (기본 2% = 0.02)
            risk_reward_ratio: 리스크 대비 보상 비율 (기본 1.5)
        """
        if initial_balance <= 0:
            raise ValueError("초기 잔고는 0보다 커야 합니다")
        
        if not (0 < risk_percent <= 1):
            raise ValueError("risk_percent는 0 초과 1 이하여야 합니다")
        
        if risk_reward_ratio <= 0:
            raise ValueError("risk_reward_ratio는 0보다 커야 합니다")
        
        self.initial_balance = initial_balance
        self.risk_percent = risk_percent
        self.risk_reward_ratio = risk_reward_ratio
    
    def calculate_position_size(
        self, 
        entry_price: float, 
        stop_loss: float
    ) -> Tuple[float, float]:
        """
        포지션 크기 계산
        
        Args:
            entry_price: 진입 가격
            stop_loss: 손절 가격
        
        Returns:
            (position_size, risk) 튜플
            
        Note:
            risk == 0 인 경우 position_size = 0 반환
            이 경우 호출자는 진입을 스킵하고 warning을 기록해야 함
        """
        if entry_price <= 0:
            raise ValueError("entry_price는 양수여야 합니다")
        
        if stop_loss <= 0:
            raise ValueError("stop_loss는 양수여야 합니다")
        
        # 리스크 계산
        risk = abs(entry_price - stop_loss)
        
        # risk가 0인 경우 처리 (division by zero 방지)
        if risk == 0:
            return 0.0, 0.0
        
        # 포지션 크기 계산
        # 공식: (초기 자산 * 리스크 비율) / 리스크
        # 예: (10000 * 0.02) / 100 = 2 계약
        position_size = (self.initial_balance * self.risk_percent) / risk
        
        return position_size, risk
    
    def calculate_tp1_price(
        self, 
        entry_price: float, 
        stop_loss: float, 
        direction: Direction
    ) -> float:
        """
        TP1 가격 계산
        
        Args:
            entry_price: 진입 가격
            stop_loss: 손절 가격
            direction: 포지션 방향
        
        Returns:
            TP1 가격
            
        Note:
            Risk Reward Ratio = 1.5 고정
            reward = risk × 1.5
            
            LONG: TP1 = entry_price + reward
            SHORT: TP1 = entry_price - reward
        """
        if entry_price <= 0:
            raise ValueError("entry_price는 양수여야 합니다")
        
        if stop_loss <= 0:
            raise ValueError("stop_loss는 양수여야 합니다")
        
        # 리스크 계산
        risk = abs(entry_price - stop_loss)
        
        # 보상 계산
        reward = risk * self.risk_reward_ratio
        
        # 방향에 따라 TP1 계산
        if direction == 'LONG':
            return entry_price + reward
        else:  # SHORT
            return entry_price - reward
    
    def move_sl_to_be(self, position: Position) -> None:
        """
        손절가를 진입가(BE)로 이동
        
        TP1 도달 시 호출되어 잔여 50% 포지션의 손절가를
        진입가로 이동함 (무손실 보장)
        
        Args:
            position: 현재 포지션 (in-place 수정)
        """
        if position is None:
            raise ValueError("position이 None입니다")
        
        # SL을 진입가로 이동
        position.stop_loss = position.entry_price
        
        # TP1 도달 플래그 설정
        position.tp1_hit = True

