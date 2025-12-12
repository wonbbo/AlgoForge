"""
성과 지표 계산 모듈
"""
from typing import List
from dataclasses import dataclass
from ..models.trade import Trade


@dataclass
class Metrics:
    """
    성과 지표
    
    Attributes:
        trades_count: 총 거래 수
        winning_trades: 승리 거래 수 (PnL > 0)
        losing_trades: 손실 거래 수 (PnL <= 0)
        win_rate: 승률 (winning_trades / trades_count)
        tp1_hit_rate: TP1 도달률
        be_exit_rate: BE 청산 비율
        total_pnl: 총 손익
        average_pnl: 평균 손익
        profit_factor: 수익 팩터 (총 수익 / 총 손실)
        max_drawdown: 최대 낙폭
        score: 전략 점수 (0~100)
        grade: 등급 (S/A/B/C/D)
    """
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


class MetricsCalculator:
    """
    Metrics 계산 클래스
    
    거래 목록으로부터 성과 지표를 계산
    """
    
    def calculate(self, trades: List[Trade]) -> Metrics:
        """
        거래 목록으로부터 성과 지표를 계산합니다.
        
        Args:
            trades: 거래 목록
        
        Returns:
            Metrics 객체
        
        Note:
            trades_count가 0인 경우:
            - win_rate = 0
            - tp1_hit_rate = 0
            - be_exit_rate = 0
            - profit_factor = 0
            - 기타 지표도 0 또는 기본값
        """
        trades_count = len(trades)
        
        # trades가 없는 경우
        if trades_count == 0:
            return Metrics(
                trades_count=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                tp1_hit_rate=0.0,
                be_exit_rate=0.0,
                total_pnl=0.0,
                average_pnl=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                score=0.0,
                grade='D'
            )
        
        # 기본 통계
        winning_trades = sum(1 for t in trades if t.is_winning_trade())
        losing_trades = trades_count - winning_trades
        win_rate = winning_trades / trades_count
        
        # TP1 hit rate
        tp1_hit_trades = sum(1 for t in trades if t.has_tp1_hit())
        tp1_hit_rate = tp1_hit_trades / trades_count
        
        # BE exit rate
        be_exit_trades = sum(1 for t in trades if t.has_be_exit())
        be_exit_rate = be_exit_trades / trades_count
        
        # PnL 계산
        total_pnl = sum(t.calculate_total_pnl() for t in trades)
        average_pnl = total_pnl / trades_count
        
        # Profit Factor
        total_profit = sum(
            t.calculate_total_pnl() for t in trades 
            if t.calculate_total_pnl() > 0
        )
        total_loss = abs(sum(
            t.calculate_total_pnl() for t in trades 
            if t.calculate_total_pnl() <= 0
        ))
        
        # total_loss가 0이면 profit_factor는 0으로 설정
        # (손실이 없으면 의미 없는 지표)
        profit_factor = total_profit / total_loss if total_loss > 0 else 0.0
        
        # Max Drawdown
        max_drawdown = self._calculate_max_drawdown(trades)
        
        # Score 계산
        score = self._calculate_score(
            win_rate, 
            tp1_hit_rate, 
            profit_factor, 
            max_drawdown
        )
        
        # Grade 매핑
        grade = self._get_grade(score)
        
        return Metrics(
            trades_count=trades_count,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            tp1_hit_rate=tp1_hit_rate,
            be_exit_rate=be_exit_rate,
            total_pnl=total_pnl,
            average_pnl=average_pnl,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            score=score,
            grade=grade
        )
    
    def _calculate_max_drawdown(self, trades: List[Trade]) -> float:
        """
        최대 낙폭 계산
        
        Args:
            trades: 거래 목록
        
        Returns:
            최대 낙폭 (절대값)
            
        Note:
            누적 PnL의 peak 대비 최대 하락폭을 계산
        """
        if not trades:
            return 0.0
        
        cumulative_pnl = 0.0
        peak = 0.0
        max_dd = 0.0
        
        for trade in trades:
            cumulative_pnl += trade.calculate_total_pnl()
            
            # 새로운 peak 갱신
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            
            # 현재 drawdown 계산
            dd = peak - cumulative_pnl
            
            # 최대 drawdown 갱신
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_score(
        self, 
        win_rate: float, 
        tp1_hit_rate: float, 
        profit_factor: float, 
        max_drawdown: float
    ) -> float:
        """
        전략 점수 계산 (0~100)
        
        Args:
            win_rate: 승률 (0~1)
            tp1_hit_rate: TP1 도달률 (0~1)
            profit_factor: 수익 팩터
            max_drawdown: 최대 낙폭
        
        Returns:
            점수 (0~100)
            
        Note:
            가중치:
            - win_rate: 30%
            - tp1_hit_rate: 20%
            - profit_factor: 30%
            - max_drawdown: 20%
        """
        # 정규화 (0~100 스케일)
        win_rate_score = win_rate * 100
        tp1_hit_rate_score = tp1_hit_rate * 100
        
        # Profit Factor는 5 이상이면 100점 만점
        profit_factor_score = min(profit_factor * 20, 100)
        
        # Max DD는 낮을수록 좋음
        # 간단한 처리: DD가 100 이상이면 0점, 0이면 100점
        # 실제로는 초기 자산 대비 비율로 계산하는 것이 더 정확하지만
        # MVP에서는 단순화
        dd_score = max(100 - max_drawdown / 10, 0)
        
        # 가중 평균
        score = (
            win_rate_score * 0.3 +
            tp1_hit_rate_score * 0.2 +
            profit_factor_score * 0.3 +
            dd_score * 0.2
        )
        
        return round(score, 2)
    
    def _get_grade(self, score: float) -> str:
        """
        점수에 따른 등급 반환
        
        Args:
            score: 점수 (0~100)
        
        Returns:
            등급 (S/A/B/C/D)
            
        Note:
            S: 85~100
            A: 70~84
            B: 55~69
            C: 40~54
            D: <40
        """
        if score >= 85:
            return 'S'
        elif score >= 70:
            return 'A'
        elif score >= 55:
            return 'B'
        elif score >= 40:
            return 'C'
        else:
            return 'D'

