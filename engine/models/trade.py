"""
거래(Trade) 모델
"""
from dataclasses import dataclass, field
from typing import List
from .trade_leg import TradeLeg, ExitType
from .position import Direction


@dataclass
class Trade:
    """
    거래(Trade) 모델
    
    하나의 trade는 진입부터 최종 종료까지의 전체 과정
    부분 청산(TP1)도 동일한 trade에 속함
    
    Attributes:
        trade_id: 거래 ID (고유 식별자)
        direction: 포지션 방향 (LONG/SHORT)
        entry_price: 진입 가격
        entry_timestamp: 진입 시각 (UNIX timestamp)
        position_size: 포지션 크기 (계약 수)
        initial_risk: 초기 리스크
        stop_loss: 손절가
        take_profit_1: 1차 익절가
        balance_at_entry: 진입 시점의 잔고 (리스크 제한 계산용)
        leverage: 사용한 레버리지 (명목가치 / 잔고)
        legs: 거래 구간 목록 (최대 2개: TP1 + FINAL)
        is_closed: 거래 종료 여부
    """
    trade_id: int
    direction: Direction
    entry_price: float
    entry_timestamp: int
    position_size: float
    initial_risk: float
    stop_loss: float
    take_profit_1: float
    balance_at_entry: float = 0.0  # 진입 시점의 잔고 (리스크 제한 계산용)
    leverage: float = 1.0  # 사용한 레버리지 (기본값 1.0 = 레버리지 없음)
    
    # 거래 종료 정보
    legs: List[TradeLeg] = field(default_factory=list)
    is_closed: bool = False
    
    def add_leg(self, leg: TradeLeg) -> None:
        """
        trade_leg 추가
        
        Args:
            leg: 추가할 TradeLeg 객체
        """
        # 동일 trade_id 확인
        if leg.trade_id != self.trade_id:
            raise ValueError(
                f"leg의 trade_id({leg.trade_id})가 "
                f"trade의 trade_id({self.trade_id})와 일치하지 않습니다"
            )
        
        # 최대 2개까지만 허용
        if len(self.legs) >= 2:
            raise ValueError(
                f"하나의 trade는 최대 2개의 leg만 가질 수 있습니다 "
                f"(현재 {len(self.legs)}개)"
            )
        
        self.legs.append(leg)
    
    def close_trade(self) -> None:
        """거래 종료 처리"""
        self.is_closed = True
    
    def calculate_total_pnl(self) -> float:
        """
        총 PnL 계산
        
        Returns:
            모든 leg의 PnL 합계
        """
        return sum(leg.pnl for leg in self.legs)
    
    def is_winning_trade(self) -> bool:
        """
        승리 거래 여부
        
        Returns:
            총 PnL이 양수이면 True
        """
        return self.calculate_total_pnl() > 0
    
    def has_tp1_hit(self) -> bool:
        """
        TP1 도달 여부
        
        Returns:
            TP1 leg가 있으면 True
        """
        return any(leg.exit_type == 'TP1' for leg in self.legs)
    
    def has_be_exit(self) -> bool:
        """
        BE 청산 여부
        
        Returns:
            BE leg가 있으면 True
        """
        return any(leg.exit_type == 'BE' for leg in self.legs)

