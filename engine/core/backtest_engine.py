"""
백테스트 엔진 모듈
"""
from typing import List, Optional, Callable, Dict, Any
from ..models.bar import Bar
from ..models.position import Position, Direction
from ..models.trade import Trade
from ..models.trade_leg import TradeLeg, ExitType
from .risk_manager import RiskManager


class BacktestEngine:
    """
    백테스트 엔진
    
    봉 단위 시뮬레이션 기반의 결정적(deterministic) 백테스트 엔진
    동일한 입력(bars + strategy)에 대해 항상 동일한 결과를 보장함
    
    특징:
    - 단일 스레드 실행
    - Close Fill 체결만 사용
    - 동시에 하나의 포지션만 보유
    - 결정적 결과 보장
    """
    
    # 엔진 버전 (결정성 보장을 위해 명시)
    VERSION = "1.0.0"
    
    def __init__(
        self, 
        initial_balance: float,
        strategy_func: Callable[[Bar], Optional[Dict[str, Any]]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        db_conn: Optional[Any] = None,
        risk_percent: float = 0.02,
        risk_reward_ratio: float = 1.5,
        rebalance_interval: int = 50,
        exit_checker: Optional[Callable[[int, str], bool]] = None,
        atr_trailing_config: Optional[Dict[str, Any]] = None,
        atr_value_getter: Optional[Callable[[int], Optional[float]]] = None,
        timestamp_to_index: Optional[Dict[int, int]] = None
    ):
        """
        Args:
            initial_balance: 초기 자산
            strategy_func: 전략 함수
                입력: Bar
                출력: None 또는 {'direction': 'LONG'|'SHORT', 'stop_loss': float}
            progress_callback: 진행률 콜백 함수 (선택)
                입력: (processed_bars: int, total_bars: int)
                출력: None
            db_conn: 데이터베이스 연결 객체 (레버리지 데이터 로드용, 선택)
            risk_percent: 거래당 최대 손실 비율 (기본 0.02 = 2%, 프리셋에서 설정)
            risk_reward_ratio: 리스크 대비 보상 비율 (기본 1.5, 프리셋에서 설정)
            rebalance_interval: 잔고 재평가 주기 (기본 50거래, 프리셋에서 설정)
            exit_checker: 지표 기반 진출 조건 체커 함수 (선택)
                입력: (bar_index: int, direction: str)
                출력: bool (True면 진출 조건 충족)
            atr_trailing_config: ATR Trailing Stop 설정 (선택)
                {'atr_indicator_id': str, 'multiplier': float}
            atr_value_getter: ATR 값 조회 함수 (선택)
                입력: (bar_index: int)
                출력: Optional[float]
            timestamp_to_index: timestamp → bar_index 매핑 (선택)
        """
        if initial_balance <= 0:
            raise ValueError("초기 잔고는 0보다 커야 합니다")
        
        if rebalance_interval < 1:
            raise ValueError("rebalance_interval은 1 이상이어야 합니다")
        
        self.initial_balance = initial_balance
        self.strategy_func = strategy_func
        self.risk_manager = RiskManager(
            initial_balance, 
            risk_percent=risk_percent,
            risk_reward_ratio=risk_reward_ratio,
            db_conn=db_conn
        )
        self.progress_callback = progress_callback
        self.rebalance_interval = rebalance_interval
        
        # 진출 조건 관련 설정
        self.exit_checker = exit_checker
        self.atr_trailing_config = atr_trailing_config
        self.atr_value_getter = atr_value_getter
        self.timestamp_to_index = timestamp_to_index or {}
        
        # 상태 관리
        self.current_position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.trade_id_counter = 1
        
        # 거래 완료 카운터 (잔고 재평가용)
        self.completed_trades_count = 0
        
        # 경고 메시지 저장 (run_artifacts에 기록될 내용)
        self.warnings: List[str] = []
    
    def run(self, bars: List[Bar]) -> List[Trade]:
        """
        백테스트 실행
        
        Args:
            bars: 봉 데이터 리스트 (timestamp 오름차순 정렬 필수)
        
        Returns:
            거래 목록
            
        Raises:
            ValueError: bars가 비어있거나 timestamp 정렬이 안 된 경우
        """
        # 입력 검증
        if not bars:
            raise ValueError("bars가 비어있습니다")
        
        # timestamp 오름차순 정렬 확인
        for i in range(len(bars) - 1):
            if bars[i].timestamp >= bars[i + 1].timestamp:
                raise ValueError(
                    f"bars는 timestamp 오름차순으로 정렬되어야 합니다 "
                    f"(index {i}: {bars[i].timestamp} >= "
                    f"index {i+1}: {bars[i+1].timestamp})"
                )
        
        total_bars = len(bars)
        
        # 봉 단위 처리
        for idx, bar in enumerate(bars):
            self._process_bar(bar)
            
            # 진행률 콜백 호출 (업데이트 빈도: 1% 단위 또는 최소 100개 봉마다)
            if self.progress_callback:
                update_interval = max(1, total_bars // 100)
                # 마지막 봉이거나 업데이트 주기에 도달한 경우
                if (idx + 1) % update_interval == 0 or (idx + 1) == total_bars:
                    self.progress_callback(idx + 1, total_bars)
        
        return self.trades
    
    def _process_bar(self, bar: Bar) -> None:
        """
        봉 처리 (핵심 로직)
        
        처리 순서:
        1. 기존 포지션 관리
        2. SL / TP1 / Reverse 판정 (우선순위 적용)
        3. 포지션 종료 처리
        4. 신규 진입 판정
        
        Note:
            - SL로 청산된 경우: 해당 봉에서 바로 재진입 조건 체크 허용
            - REVERSE/BE로 청산된 경우: 해당 봉에서 재진입 불가 (TP1 이후이므로)
        """
        # 이 봉에서 청산된 방식 추적 (None = 청산 없음)
        closed_exit_type = None
        
        # 1. 기존 포지션이 있는 경우
        if self.current_position:
            # TP1 발생 플래그 초기화 (새로운 봉 시작)
            self.current_position.tp1_occurred_this_bar = False
            
            # 2. SL / TP1 / Reverse 판정 (우선순위 적용)
            exit_type = self._check_exit_conditions(bar)
            
            # 3. 포지션 종료 처리
            if exit_type:
                self._close_position(bar, exit_type)
                closed_exit_type = exit_type
        
        # 4. 신규 진입 판정
        # - 포지션이 없고
        # - 이 봉에서 청산되지 않았거나, SL로 청산된 경우에만 진입 조건 체크
        # - SL 청산 후에는 바로 재진입 가능 (손절 후 즉시 재진입 허용)
        # - REVERSE/BE 청산 후에는 재진입 불가 (TP1 발생 후이므로)
        if not self.current_position:
            if closed_exit_type is None or closed_exit_type == 'SL':
                self._check_entry_signal(bar)
    
    def _check_exit_conditions(self, bar: Bar) -> Optional[ExitType]:
        """
        청산 조건 체크
        
        우선순위:
        1. Stop Loss (최우선) - 일반 SL 또는 ATR Trailing SL
        2. TP1 (2순위)
        3. 지표 기반 진출 조건 (신규)
        4. ATR Trailing Stop 도달 (TP1 후에만)
        5. Reverse Signal (최후순위)
        
        Returns:
            청산 타입 또는 None
            
        Note:
            TP1은 부분 청산이므로 ExitType을 반환하지 않고
            내부적으로 처리한 후 None 반환
        """
        pos = self.current_position
        if not pos:
            return None
        
        # TP1 후 ATR Trailing이 활성화되어 있으면 trailing_stop 업데이트
        if pos.tp1_hit and self.atr_trailing_config:
            self._update_trailing_stop(bar, pos)
        
        # 1. Stop Loss 체크 (최우선) - trailing_stop도 고려
        if self._check_stop_loss(bar, pos):
            return 'SL'
        
        # 2. TP1 체크
        if not pos.tp1_hit and self._check_tp1(bar, pos):
            # TP1 발생 처리 (50% 부분 청산)
            self._handle_tp1(bar, pos)
            # TP1은 부분 청산이므로 계속 진행
            # (FINAL 종료는 아님)
            return None
        
        # 3. 지표 기반 진출 조건 체크
        if self._check_indicator_exit(bar, pos):
            # 지표 기반 진출은 EXIT_INDICATOR로 청산
            # TP1 후면 BE로, 아니면 REVERSE로 처리 (기존 exit_type 재활용)
            if pos.tp1_hit:
                return 'BE'
            else:
                return 'REVERSE'
        
        # 4. Reverse Signal 체크
        # 중요: TP1 발생 봉에서는 reverse 평가 안 함
        if not pos.tp1_occurred_this_bar:
            if self._check_reverse_signal(bar, pos):
                # TP1 후 잔여 포지션이면 BE 청산
                if pos.tp1_hit:
                    return 'BE'
                else:
                    return 'REVERSE'
        
        return None
    
    def _update_trailing_stop(self, bar: Bar, pos: Position) -> None:
        """
        ATR Trailing Stop 업데이트
        
        TP1 달성 후 매 봉마다 호출됨
        LONG: max(current_trailing, close - n × ATR)
        SHORT: min(current_trailing, close + n × ATR)
        
        Args:
            bar: 현재 봉
            pos: 현재 포지션
        """
        if not self.atr_trailing_config or not self.atr_value_getter:
            return
        
        # 봉 인덱스 가져오기
        bar_index = self.timestamp_to_index.get(bar.timestamp)
        if bar_index is None:
            return
        
        # ATR 값 가져오기
        atr_value = self.atr_value_getter(bar_index)
        if atr_value is None or atr_value <= 0:
            return
        
        multiplier = self.atr_trailing_config.get("multiplier", 2.0)
        
        if pos.direction == 'LONG':
            # LONG: max(current_trailing, close - n × ATR)
            new_trailing = bar.close - (atr_value * multiplier)
            
            # trailing_stop이 없으면 초기화 (진입가 = BE)
            if pos.trailing_stop is None:
                pos.trailing_stop = pos.entry_price
            
            # 유리한 방향(상승)으로만 업데이트
            if new_trailing > pos.trailing_stop:
                pos.trailing_stop = new_trailing
                # stop_loss도 함께 업데이트
                pos.stop_loss = pos.trailing_stop
        
        else:  # SHORT
            # SHORT: min(current_trailing, close + n × ATR)
            new_trailing = bar.close + (atr_value * multiplier)
            
            # trailing_stop이 없으면 초기화 (진입가 = BE)
            if pos.trailing_stop is None:
                pos.trailing_stop = pos.entry_price
            
            # 유리한 방향(하락)으로만 업데이트
            if new_trailing < pos.trailing_stop:
                pos.trailing_stop = new_trailing
                # stop_loss도 함께 업데이트
                pos.stop_loss = pos.trailing_stop
    
    def _check_indicator_exit(self, bar: Bar, pos: Position) -> bool:
        """
        지표 기반 진출 조건 체크
        
        Args:
            bar: 현재 봉
            pos: 현재 포지션
        
        Returns:
            bool: 진출 조건 충족 여부
        """
        if not self.exit_checker:
            return False
        
        # 봉 인덱스 가져오기
        bar_index = self.timestamp_to_index.get(bar.timestamp)
        if bar_index is None:
            return False
        
        # 진출 조건 평가
        return self.exit_checker(bar_index, pos.direction)
    
    def _check_stop_loss(self, bar: Bar, pos: Position) -> bool:
        """
        SL 도달 여부 체크
        
        Args:
            bar: 현재 봉
            pos: 현재 포지션
        
        Returns:
            SL 도달 여부
            
        Note:
            도달 판정: high / low 사용
            LONG: 저가가 SL 이하
            SHORT: 고가가 SL 이상
        """
        if pos.direction == 'LONG':
            # 롱: 저가가 SL 이하
            return bar.low <= pos.stop_loss
        else:  # SHORT
            # 숏: 고가가 SL 이상
            return bar.high >= pos.stop_loss
    
    def _check_tp1(self, bar: Bar, pos: Position) -> bool:
        """
        TP1 도달 여부 체크
        
        Args:
            bar: 현재 봉
            pos: 현재 포지션
        
        Returns:
            TP1 도달 여부
            
        Note:
            도달 판정: high / low 사용
            LONG: 고가가 TP1 이상
            SHORT: 저가가 TP1 이하
        """
        if pos.direction == 'LONG':
            # 롱: 고가가 TP1 이상
            return bar.high >= pos.take_profit_1
        else:  # SHORT
            # 숏: 저가가 TP1 이하
            return bar.low <= pos.take_profit_1
    
    def _handle_tp1(self, bar: Bar, pos: Position) -> None:
        """
        TP1 처리
        
        1. 50% 부분 청산 (TP1 leg 생성)
        2. SL을 BE로 이동
        3. 플래그 설정 (이 봉에서는 reverse 평가 안 함)
        
        Args:
            bar: 현재 봉
            pos: 현재 포지션
        """
        # 현재 trade 가져오기
        current_trade = next(
            (t for t in self.trades if t.trade_id == pos.trade_id), 
            None
        )
        if not current_trade:
            self.warnings.append(
                f"timestamp={bar.timestamp}: "
                f"trade_id={pos.trade_id}를 찾을 수 없습니다"
            )
            return
        
        # 1. TP1 leg 생성 (50% 청산)
        qty_ratio = 0.5
        pnl = self._calculate_pnl(
            pos.entry_price, 
            bar.close,  # Close Fill
            pos.direction, 
            pos.position_size * qty_ratio
        )
        
        tp1_leg = TradeLeg(
            trade_id=pos.trade_id,
            exit_type='TP1',
            exit_timestamp=bar.timestamp,
            exit_price=bar.close,
            qty_ratio=qty_ratio,
            pnl=pnl
        )
        current_trade.add_leg(tp1_leg)
        
        # 2. SL을 BE로 이동
        self.risk_manager.move_sl_to_be(pos)
        
        # 3. 플래그 설정 (이 봉에서는 reverse 평가 안 함)
        pos.tp1_occurred_this_bar = True
    
    def _check_reverse_signal(self, bar: Bar, pos: Position) -> bool:
        """
        반대 방향 신호 체크
        
        Args:
            bar: 현재 봉
            pos: 현재 포지션
        
        Returns:
            반대 방향 신호 발생 여부
        """
        signal = self.strategy_func(bar)
        
        if signal is None:
            return False
        
        # direction 키가 없으면 무시
        if 'direction' not in signal:
            return False
        
        signal_direction = signal['direction']
        
        # 반대 방향인지 체크
        if pos.direction == 'LONG' and signal_direction == 'SHORT':
            return True
        elif pos.direction == 'SHORT' and signal_direction == 'LONG':
            return True
        
        return False
    
    def _close_position(self, bar: Bar, exit_type: ExitType) -> None:
        """
        포지션 종료 처리
        
        FINAL leg 생성 및 trade 종료
        
        Args:
            bar: 현재 봉
            exit_type: 청산 타입 (SL, BE, REVERSE)
        """
        pos = self.current_position
        if not pos:
            return
        
        # 현재 trade 가져오기
        current_trade = next(
            (t for t in self.trades if t.trade_id == pos.trade_id), 
            None
        )
        if not current_trade:
            self.warnings.append(
                f"timestamp={bar.timestamp}: "
                f"trade_id={pos.trade_id}를 찾을 수 없습니다"
            )
            return
        
        # 잔여 수량 계산
        # TP1이 발생했으면 50%, 아니면 100%
        remaining_qty_ratio = 0.5 if pos.tp1_hit else 1.0
        
        # FINAL leg 생성
        pnl = self._calculate_pnl(
            pos.entry_price,
            bar.close,  # Close Fill
            pos.direction,
            pos.position_size * remaining_qty_ratio
        )
        
        final_leg = TradeLeg(
            trade_id=pos.trade_id,
            exit_type=exit_type,
            exit_timestamp=bar.timestamp,
            exit_price=bar.close,
            qty_ratio=remaining_qty_ratio,
            pnl=pnl
        )
        current_trade.add_leg(final_leg)
        current_trade.close_trade()
        
        # 포지션 초기화
        self.current_position = None
        
        # 거래 완료 카운터 증가
        self.completed_trades_count += 1
        
        # 설정된 주기마다 잔고 재평가
        if self.completed_trades_count % self.rebalance_interval == 0:
            # 현재 잔고 = 초기 자산 + 모든 완료된 거래의 누적 PnL
            total_pnl = sum(t.calculate_total_pnl() for t in self.trades)
            current_balance = self.initial_balance + total_pnl
            
            # RiskManager의 잔고 업데이트
            self.risk_manager.update_balance(current_balance)
    
    def _check_entry_signal(self, bar: Bar) -> None:
        """
        신규 진입 신호 체크 및 처리
        
        Args:
            bar: 현재 봉
        """
        signal = self.strategy_func(bar)
        
        if signal is None:
            return
        
        # direction과 stop_loss 키가 있는지 확인
        if 'direction' not in signal or 'stop_loss' not in signal:
            self.warnings.append(
                f"timestamp={bar.timestamp}: "
                f"신호에 'direction' 또는 'stop_loss'가 없습니다"
            )
            return
        
        direction = signal['direction']
        stop_loss = signal['stop_loss']
        
        # direction이 유효한지 확인
        if direction not in ('LONG', 'SHORT'):
            self.warnings.append(
                f"timestamp={bar.timestamp}: "
                f"유효하지 않은 direction={direction}"
            )
            return
        
        # 포지션 진입 (Close Fill)
        self._enter_position(bar, direction, stop_loss)
    
    def _enter_position(
        self, 
        bar: Bar, 
        direction: Direction, 
        stop_loss: float
    ) -> None:
        """
        포지션 진입
        
        Args:
            bar: 현재 봉
            direction: 진입 방향
            stop_loss: 손절가
        """
        entry_price = bar.close  # Close Fill
        
        # 입력 검증
        if stop_loss <= 0:
            self.warnings.append(
                f"timestamp={bar.timestamp}: "
                f"stop_loss={stop_loss}는 양수여야 합니다. 진입 스킵"
            )
            return
        
        # LONG의 경우 SL < entry 확인
        if direction == 'LONG' and stop_loss >= entry_price:
            self.warnings.append(
                f"timestamp={bar.timestamp}: "
                f"LONG 포지션에서 stop_loss({stop_loss})가 "
                f"entry_price({entry_price})보다 크거나 같습니다. 진입 스킵"
            )
            return
        
        # SHORT의 경우 SL > entry 확인
        if direction == 'SHORT' and stop_loss <= entry_price:
            self.warnings.append(
                f"timestamp={bar.timestamp}: "
                f"SHORT 포지션에서 stop_loss({stop_loss})가 "
                f"entry_price({entry_price})보다 작거나 같습니다. 진입 스킵"
            )
            return
        
        # 포지션 크기 및 레버리지 계산
        position_size, risk, leverage = self.risk_manager.calculate_position_size(
            entry_price, 
            stop_loss,
            return_leverage=True
        )
        
        # risk == 0 인 경우 진입 스킵
        if risk == 0:
            self.warnings.append(
                f"timestamp={bar.timestamp}: "
                f"risk=0이므로 진입 스킵 "
                f"(entry_price={entry_price}, stop_loss={stop_loss})"
            )
            return
        
        # TP1 계산
        tp1_price = self.risk_manager.calculate_tp1_price(
            entry_price, 
            stop_loss, 
            direction
        )
        
        # Position 생성
        position = Position(
            trade_id=self.trade_id_counter,
            direction=direction,
            entry_price=entry_price,
            entry_timestamp=bar.timestamp,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit_1=tp1_price,
            initial_risk=risk
        )
        self.current_position = position
        
        # Trade 생성 (레버리지 정보 포함)
        trade = Trade(
            trade_id=self.trade_id_counter,
            direction=direction,
            entry_price=entry_price,
            entry_timestamp=bar.timestamp,
            position_size=position_size,
            initial_risk=risk,
            stop_loss=stop_loss,
            take_profit_1=tp1_price,
            balance_at_entry=self.risk_manager.current_balance,  # 진입 시점의 잔고 저장
            leverage=leverage  # 사용한 레버리지 저장
        )
        self.trades.append(trade)
        
        # trade_id 증가
        self.trade_id_counter += 1
    
    def _calculate_pnl(
        self, 
        entry_price: float, 
        exit_price: float, 
        direction: Direction, 
        position_size: float
    ) -> float:
        """
        PnL 계산
        
        Args:
            entry_price: 진입 가격
            exit_price: 청산 가격
            direction: 방향
            position_size: 포지션 크기
        
        Returns:
            PnL (손익)
            
        Note:
            LONG: (exit_price - entry_price) × position_size
            SHORT: (entry_price - exit_price) × position_size
        """
        if direction == 'LONG':
            return (exit_price - entry_price) * position_size
        else:  # SHORT
            return (entry_price - exit_price) * position_size

