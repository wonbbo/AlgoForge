"""
리스크 관리 모듈
"""
from typing import Tuple, List, Optional, Any
from ..models.position import Position, Direction
from ..utils.leverage_loader import (
    LeverageBracket, 
    load_leverage_brackets_from_db, 
    get_max_leverage_for_notional,
    calculate_required_margin
)


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
        risk_reward_ratio: float = 1.5,
        db_conn: Optional[Any] = None
    ):
        """
        Args:
            initial_balance: 초기 자산
            risk_percent: 1 트레이드 최대 손실 비율 (기본 2% = 0.02, 프리셋에서 설정)
            risk_reward_ratio: 리스크 대비 보상 비율 (기본 1.5, 프리셋에서 설정)
            db_conn: 데이터베이스 연결 객체 (레버리지 데이터 로드용, 선택)
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
        
        # 현재 잔고 (50거래마다 재평가됨)
        self.current_balance = initial_balance
        
        # 레버리지 구간 테이블 로드 (DB에서)
        self.leverage_brackets: Optional[List[LeverageBracket]] = None
        if db_conn:
            try:
                self.leverage_brackets = load_leverage_brackets_from_db(db_conn)
            except Exception as e:
                # 레버리지 데이터 로드 실패 시 경고만 하고 계속 진행
                # (레버리지 제약 없이 실행)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"레버리지 테이블 로드 실패: {str(e)}. 레버리지 제약 없이 실행합니다.")
    
    def calculate_position_size(
        self, 
        entry_price: float, 
        stop_loss: float,
        return_leverage: bool = False
    ) -> Tuple[float, float] | Tuple[float, float, float]:
        """
        포지션 크기 계산 (레버리지 제약 적용)
        
        Args:
            entry_price: 진입 가격
            stop_loss: 손절 가격
        
        Returns:
            return_leverage=True  -> (position_size, risk, leverage)
            return_leverage=False -> (position_size, risk)
            
        Note:
            risk == 0 인 경우 position_size = 0, leverage = 1.0 반환
            이 경우 호출자는 진입을 스킵하고 warning을 기록해야 함
            
            50거래마다 재평가된 current_balance를 기준으로 포지션 크기 계산
            
            레버리지 제약이 설정된 경우:
            1. 리스크 기반 포지션 크기 계산
            2. 해당 포지션의 명목가치에 대한 최대 레버리지 조회
            3. 필요 증거금 계산
            4. 현재 잔고로 감당 가능한지 확인 후 조정
            
            레버리지 계산:
            leverage = (position_size * entry_price) / current_balance
        """
        if entry_price <= 0:
            raise ValueError("entry_price는 양수여야 합니다")
        
        if stop_loss <= 0:
            raise ValueError("stop_loss는 양수여야 합니다")
        
        # 리스크 계산
        risk = abs(entry_price - stop_loss)
        
        # risk가 0인 경우 처리 (division by zero 방지)
        if risk == 0:
            return (0.0, 0.0, 1.0) if return_leverage else (0.0, 0.0)
        
        # 포지션 크기 계산 (리스크 기반)
        # 공식: (현재 잔고 * 리스크 비율) / 리스크
        # 예: (1000 * 0.02) / 100 = 0.2 계약
        # 50거래마다 current_balance가 재평가됨
        position_size_raw = (self.current_balance * self.risk_percent) / risk
        
        # 레버리지 제약 적용
        if self.leverage_brackets:
            position_size_raw = self._apply_leverage_constraint(
                position_size_raw, 
                entry_price
            )
        
        # 포지션 크기를 정수로 변환
        # 반올림을 사용하되, 변환 후 레버리지 제약을 다시 확인하여 초과하면 내림 사용
        position_size = round(position_size_raw)
        
        # 반올림 후 0이 되는 경우 처리 (최소 1 계약)
        if position_size == 0 and position_size_raw > 0:
            if self.leverage_brackets:
                from engine.utils.leverage_loader import get_max_leverage_for_notional
                
                # 1 계약의 명목가치
                notional_for_one = 1.0 * entry_price
                
                # 1 계약에 대한 최대 레버리지
                max_lev = get_max_leverage_for_notional(self.leverage_brackets, notional_for_one)
                max_lev = int(max_lev)
                
                # 필요한 증거금 = 명목가치 / 레버리지
                required_margin = notional_for_one / max_lev
                
                # 현재 잔고로 1 계약 진입이 가능하면 허용
                if required_margin <= self.current_balance:
                    position_size = 1
            else:
                position_size = 1
        
        # 반올림 후 레버리지 제약 재확인 (반올림으로 인한 초과 방지)
        # 정수 레버리지만 사용 가능하므로, 실제 사용 레버리지 기준으로 포지션 크기 조정 또는 레버리지 상향
        actual_leverage = None  # 위에서 계산된 실제 사용 레버리지 (나중에 재사용)
        
        if position_size > 0 and self.leverage_brackets:
            from engine.utils.leverage_loader import get_max_leverage_for_notional
            import math
            
            # 반올림된 포지션의 명목가치
            notional_rounded = position_size * entry_price
            
            # 실제 사용할 레버리지 계산 (정수, 내림 처리)
            # 예: 명목가치 146,575 / 잔고 42,111 = 3.48 -> 3x
            calculated_leverage_raw = notional_rounded / self.current_balance
            calculated_leverage = int(calculated_leverage_raw)  # 정수 레버리지 (내림)
            
            # 최소 1x 레버리지
            if calculated_leverage < 1:
                calculated_leverage = 1
            
            # 반올림된 명목가치에 해당하는 bracket의 최대 레버리지 조회
            max_lev_raw = get_max_leverage_for_notional(self.leverage_brackets, notional_rounded)
            max_lev = int(max_lev_raw)  # bracket의 최대 레버리지 (정수)
            
            # 실제 사용 레버리지가 bracket의 최대 레버리지를 초과할 수 없음
            actual_leverage = min(calculated_leverage, max_lev)
            
            # 실제 사용 레버리지로 확보 가능한 최대 명목가치
            # 공식: max_allowed_notional = current_balance × 실제_사용_레버리지
            max_allowed_notional = self.current_balance * actual_leverage
            
            # 반올림된 명목가치가 실제 사용 레버리지로 확보 가능한 금액을 초과하면 조정
            if notional_rounded > max_allowed_notional:
                # 먼저 레버리지를 올려서 허용 가능한 명목가치를 늘림 (bracket의 최대 레버리지까지)
                # 예: 3x로 부족하면 4x, 5x... 최대 bracket의 최대 레버리지까지 시도
                for test_leverage in range(actual_leverage + 1, max_lev + 1):
                    test_max_notional = self.current_balance * test_leverage
                    if notional_rounded <= test_max_notional:
                        # 이 레버리지로 가능하므로 사용
                        actual_leverage = test_leverage
                        max_allowed_notional = test_max_notional
                        break
                
                # 레버리지를 올려도 부족하면 포지션 크기를 줄임
                if notional_rounded > max_allowed_notional:
                    # 내림으로 재계산
                    position_size = math.floor(position_size_raw)
                    
                    # 내림 후 명목가치 재계산
                    notional_floored = position_size * entry_price
                    
                    # 내림 후에도 초과하는지 재확인
                    if notional_floored > max_allowed_notional:
                        # 최대 가능 포지션 크기로 설정 (실제 사용 레버리지로 확보 가능한 금액 안쪽)
                        position_size = math.floor(max_allowed_notional / entry_price)
                        
                        # 포지션 크기가 0이 되는 경우 방지
                        if position_size == 0:
                            # 1 계약의 명목가치로 최대 레버리지 재확인
                            notional_for_one = 1.0 * entry_price
                            max_lev_one = get_max_leverage_for_notional(self.leverage_brackets, notional_for_one)
                            max_lev_one = int(max_lev_one)
                            max_allowed_one = self.current_balance * max_lev_one
                            
                            # 1 계약이 가능하면 허용
                            if notional_for_one <= max_allowed_one:
                                position_size = 1
                                # 1 계약의 명목가치에 맞는 레버리지 재계산
                                actual_leverage = int(notional_for_one / self.current_balance)
                                if actual_leverage < 1:
                                    actual_leverage = 1
                                actual_leverage = min(actual_leverage, max_lev_one)
                            else:
                                # 1 계약도 불가능하면 레버리지를 올려서 시도
                                for test_leverage in range(1, max_lev_one + 1):
                                    test_max_notional = self.current_balance * test_leverage
                                    if notional_for_one <= test_max_notional:
                                        position_size = 1
                                        actual_leverage = test_leverage
                                        break
                        else:
                            # 포지션 크기 조정 후 명목가치와 레버리지 재계산
                            notional_adjusted = position_size * entry_price
                            calculated_leverage_adjusted = int(notional_adjusted / self.current_balance)
                            if calculated_leverage_adjusted < 1:
                                calculated_leverage_adjusted = 1
                            max_lev_adjusted = get_max_leverage_for_notional(self.leverage_brackets, notional_adjusted)
                            max_lev_adjusted = int(max_lev_adjusted)
                            actual_leverage = min(calculated_leverage_adjusted, max_lev_adjusted)
        
        # 실제 사용된 레버리지 계산
        # 위에서 이미 계산된 actual_leverage를 사용하거나, 새로 계산
        notional_value = position_size * entry_price
        
        # 잔고가 0 이하인 경우 레버리지를 1로 설정 (예외 처리)
        if self.current_balance <= 0:
            leverage = 1
        else:
            # 위에서 계산된 actual_leverage가 있으면 사용
            if actual_leverage is not None:
                leverage = actual_leverage
            elif self.leverage_brackets:
                # 새로 계산
                calculated_leverage_raw = notional_value / self.current_balance
                calculated_leverage = int(calculated_leverage_raw)
                
                # 최소 1x 레버리지
                if calculated_leverage < 1:
                    calculated_leverage = 1
                
                # bracket의 최대 레버리지 조회
                max_lev_raw = get_max_leverage_for_notional(self.leverage_brackets, notional_value)
                max_lev = int(max_lev_raw)
                
                # bracket의 최대 레버리지를 초과할 수 없음
                leverage = min(calculated_leverage, max_lev)
            else:
                # 레버리지 bracket이 없는 경우 정수로 내림 처리
                calculated_leverage = notional_value / self.current_balance
                leverage = int(calculated_leverage)
                
                # 최소 1x 레버리지
                if leverage < 1:
                    leverage = 1
        
        if return_leverage:
            return float(position_size), risk, float(leverage)
        return float(position_size), risk
    
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
    
    def update_balance(self, new_balance: float) -> None:
        """
        현재 잔고 업데이트
        
        50거래마다 호출되어 총자산을 재평가함
        재평가된 잔고를 기준으로 이후 포지션 크기가 계산됨
        
        Args:
            new_balance: 새로운 잔고 (초기 자산 + 누적 PnL)
        
        Note:
            레버리지를 사용한다는 가정하에 잔고가 0 이하가 되어도 허용
            (실제 파산 로직은 향후 확장 시 추가)
        """
        self.current_balance = new_balance
    
    def _apply_leverage_constraint(
        self, 
        position_size: float, 
        entry_price: float
    ) -> float:
        """
        레버리지 제약 적용하여 포지션 크기 조정
        
        Args:
            position_size: 리스크 기반으로 계산된 포지션 크기
            entry_price: 진입 가격
        
        Returns:
            레버리지 제약이 적용된 포지션 크기
        
        Note:
            반복적으로 적용하여 최종 포지션 크기가 올바른 bracket에 속하도록 보장
            
            1. 포지션 명목가치 계산
            2. 해당 구간의 최대 레버리지 조회 (정수)
            3. 현재 잔고로 얻을 수 있는 최대 명목가치 계산: current_balance * max_leverage
            4. 리스크 기반 명목가치가 이를 초과하면 제한
            5. 제한된 포지션이 다른 bracket에 속할 수 있으므로 재확인
        """
        if not self.leverage_brackets:
            return position_size
        
        # 최대 10번 반복 (무한 루프 방지)
        adjusted_position_size = position_size
        
        for _ in range(10):
            # 현재 포지션의 명목가치 계산
            notional_value = adjusted_position_size * entry_price
            
            # 해당 명목가치에 대한 최대 레버리지 조회
            max_leverage = get_max_leverage_for_notional(self.leverage_brackets, notional_value)
            
            # 레버리지는 정수여야 함
            max_leverage = int(max_leverage)
            
            # 현재 잔고로 사용 가능한 최대 명목가치
            # 공식: max_notional = current_balance × max_leverage
            max_notional = self.current_balance * max_leverage
            
            # 리스크 기반 명목가치가 한도를 초과하는지 확인
            if notional_value <= max_notional:
                # 현재 포지션 크기로 진입 가능
                return adjusted_position_size
            
            # 한도를 초과하면 포지션 크기를 제한
            # 공식: adjusted_position_size = max_notional / entry_price
            new_position_size = max_notional / entry_price
            
            # 포지션 크기가 더 이상 변하지 않으면 수렴한 것으로 간주
            if abs(new_position_size - adjusted_position_size) < 0.01:
                return new_position_size
            
            adjusted_position_size = new_position_size
        
        # 최대 반복 횟수 도달 (드문 경우)
        return adjusted_position_size

