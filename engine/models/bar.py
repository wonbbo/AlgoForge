"""
봉(Bar) 데이터 모델
"""
from dataclasses import dataclass


@dataclass
class Bar:
    """
    봉(Bar) 데이터 모델
    
    Attributes:
        timestamp: 봉의 시작 시간 (UNIX timestamp, 초 단위)
        open: 시가 (do)
        high: 고가 (dh)
        low: 저가 (dl)
        close: 종가 (dc)
        volume: 거래량 (dv)
        direction: 봉 방향 (dd: 1=상승, -1=하락, 0=보합)
    """
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    direction: int
    
    def __post_init__(self):
        """데이터 검증"""
        # timestamp는 양수여야 함
        if self.timestamp < 0:
            raise ValueError("timestamp는 0 이상이어야 합니다")
        
        # OHLC 데이터 검증
        if self.high < self.low:
            raise ValueError("high는 low보다 크거나 같아야 합니다")
        
        if not (self.low <= self.open <= self.high):
            raise ValueError("open은 low와 high 사이에 있어야 합니다")
        
        if not (self.low <= self.close <= self.high):
            raise ValueError("close는 low와 high 사이에 있어야 합니다")
        
        # volume은 0 이상이어야 함
        if self.volume < 0:
            raise ValueError("volume은 0 이상이어야 합니다")
        
        # direction은 -1, 0, 1 중 하나
        if self.direction not in (-1, 0, 1):
            raise ValueError("direction은 -1, 0, 1 중 하나여야 합니다")

