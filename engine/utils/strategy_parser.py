"""
전략 파서(Strategy Parser) 모듈

Strategy JSON을 파싱하여 신호를 생성합니다.

멀티 타임프레임(MTF) 지원:
  - 인디케이터 정의에 "timeframe" 필드 추가 가능 (없으면 "base")
  - 조건식 ref에 "@1h" 등 접미사 지정 가능 (없으면 "base")
  - HTF 값은 "이미 닫힌 마지막 HTF 봉" 기준 — look-ahead 구조적 차단
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
import pandas as pd
from ..models.bar import Bar
from .indicators import IndicatorCalculator
from .htf_mapper import build_htf_index_map, interval_to_seconds
import logging

logger = logging.getLogger(__name__)


BASE_TF = "base"


class StrategyParser:
    """
    전략 파서

    Strategy JSON을 파싱하여 봉마다 진입 신호를 생성합니다.
    단일 타임프레임과 멀티 타임프레임(MTF) 모두 지원.
    """

    def __init__(
        self,
        strategy_definition: Dict[str, Any],
        bars: List[Bar],
        df: Optional[pd.DataFrame] = None,
        htf_data: Optional[Dict[str, Tuple[List[Bar], pd.DataFrame]]] = None,
    ):
        """
        Args:
            strategy_definition: 전략 정의 JSON
            bars: 베이스 타임프레임 봉 리스트
            df: 베이스 OHLCV DataFrame (지표 계산용). 없으면 bars에서 자동 생성
            htf_data: 상위 타임프레임 데이터 (선택)
                key: 타임프레임 문자열 (예: "1h", "1d")
                value: (bars, df) 튜플
        """
        self.definition = strategy_definition
        self.bars = bars
        # df가 없으면 bars로부터 DataFrame 생성 (테스트 호환성)
        if df is None:
            self.df = pd.DataFrame(
                {
                    'open': [b.open for b in bars],
                    'high': [b.high for b in bars],
                    'low': [b.low for b in bars],
                    'close': [b.close for b in bars],
                    'volume': [b.volume for b in bars],
                    'direction': [b.direction for b in bars],
                },
                index=pd.to_datetime([b.timestamp for b in bars], unit='s')
            )
        else:
            self.df = df

        # 베이스 TF의 timestamp -> index 매핑
        self.timestamp_to_index = {bar.timestamp: i for i, bar in enumerate(bars)}

        # ----- MTF 구조 -----
        # 타임프레임별 IndicatorCalculator 보관. key="base" 는 항상 존재.
        self.indicator_calcs: Dict[str, IndicatorCalculator] = {
            BASE_TF: IndicatorCalculator(self.df),
        }
        # 타임프레임별 봉 리스트 (HTF 값 조회 시 사용)
        self.tf_bars: Dict[str, List[Bar]] = {BASE_TF: bars}
        # base_bar_index -> htf_bar_index 매핑 (look-ahead 차단 보장)
        self.htf_index_maps: Dict[str, List[int]] = {}

        if htf_data:
            for tf, (htf_bars, htf_df) in htf_data.items():
                if tf == BASE_TF:
                    raise ValueError(f"'base'는 htf_data의 키로 사용할 수 없습니다")
                if htf_df is None:
                    htf_df = pd.DataFrame(
                        {
                            'open': [b.open for b in htf_bars],
                            'high': [b.high for b in htf_bars],
                            'low': [b.low for b in htf_bars],
                            'close': [b.close for b in htf_bars],
                            'volume': [b.volume for b in htf_bars],
                            'direction': [b.direction for b in htf_bars],
                        },
                        index=pd.to_datetime([b.timestamp for b in htf_bars], unit='s')
                    )
                self.indicator_calcs[tf] = IndicatorCalculator(htf_df)
                self.tf_bars[tf] = htf_bars
                self.htf_index_maps[tf] = build_htf_index_map(
                    base_bars=bars,
                    htf_bars=htf_bars,
                    htf_interval_sec=interval_to_seconds(tf),
                )
                logger.info(
                    f"[MTF] HTF '{tf}' 등록: {len(htf_bars)} bars, "
                    f"mapping start={self.htf_index_maps[tf][0] if bars else 'n/a'}"
                )

        # 하위호환: 기존 코드가 self.indicator_calc (단수)를 참조할 수 있음
        self.indicator_calc = self.indicator_calcs[BASE_TF]

        # 커스텀 지표 동적 로드 (모든 TF의 calculator에 등록)
        self._load_custom_indicators()

        # 지표 계산
        self._calculate_indicators()

        # 이전 지표 값 (cross 판정용)
        self.prev_indicator_values: Dict[str, float] = {}
    
    def _load_custom_indicators(self) -> None:
        """
        데이터베이스에서 커스텀 지표를 로드하여 각 TF의 calculator에 등록

        Note:
            DB 파일이 없거나 로드 실패 시에도 백테스트는 계속 진행됩니다.
        """
        from pathlib import Path
        from .indicator_loader import register_custom_indicators

        db_path = Path("db/algoforge.db")

        if not db_path.exists():
            logger.debug(f"데이터베이스 파일이 없습니다: {db_path}")
            return

        try:
            # 모든 TF의 calculator에 동일한 커스텀 지표 등록
            total = 0
            for tf, calc in self.indicator_calcs.items():
                count = register_custom_indicators(calc, str(db_path))
                total = count  # count는 DB의 지표 수이므로 TF마다 동일
            logger.debug(f"커스텀 지표 {total}개 로드 완료 (TF 수: {len(self.indicator_calcs)})")
        except Exception as e:
            logger.warning(f"커스텀 지표 로드 실패: {e}")

    def _calculate_indicators(self) -> None:
        """
        전략에 정의된 모든 지표를 해당 TF의 calculator에서 사전 계산합니다.

        인디케이터 JSON의 "timeframe" 필드로 대상 TF 선택 (없으면 "base").
        """
        indicators = self.definition.get("indicators", [])
        logger.info(f"[전략 파싱] 지표 계산 시작: {len(indicators)}개")

        for indicator in indicators:
            if not indicator.get("id") or not indicator.get("type"):
                logger.warning(f"지표 정의가 불완전합니다: {indicator}")
                continue

            indicator_id = indicator.get('id')
            indicator_type = indicator.get('type')
            tf = indicator.get('timeframe', BASE_TF) or BASE_TF

            if tf not in self.indicator_calcs:
                raise RuntimeError(
                    f"지표 '{indicator_id}'가 타임프레임 '{tf}'를 요구하지만 "
                    f"해당 TF 데이터가 제공되지 않았습니다. "
                    f"사용 가능: {list(self.indicator_calcs.keys())}"
                )

            logger.info(
                f"[전략 파싱] 지표 계산: id={indicator_id}, type={indicator_type}, tf={tf}"
            )

            try:
                self.indicator_calcs[tf].calculate_indicator(indicator)
            except Exception as e:
                error_message = (
                    f"지표 계산 실패 - ID: '{indicator_id}', Type: '{indicator_type}', "
                    f"TF: '{tf}', 에러: {str(e)}"
                )
                logger.error(error_message, exc_info=True)
                raise RuntimeError(error_message) from e

        # 계산 완료 후 base DataFrame 컬럼 출력
        indicator_columns = [
            col for col in self.df.columns
            if col not in ['open', 'high', 'low', 'close', 'volume', 'direction']
        ]
        logger.info(f"[전략 파싱] base 지표 컬럼: {indicator_columns}")
    
    def create_strategy_function(self) -> Callable[[Bar], Optional[Dict[str, Any]]]:
        """
        백테스트 엔진이 사용할 전략 함수를 생성합니다.
        
        Returns:
            Callable: strategy_func(bar) -> Optional[Dict[str, Any]]
                - None: 신호 없음
                - Dict: {'direction': 'LONG'|'SHORT', 'stop_loss': float}
        """
        def strategy_func(bar: Bar) -> Optional[Dict[str, Any]]:
            """
            봉마다 호출되는 전략 함수
            
            Args:
                bar: 현재 봉
                
            Returns:
                Optional[Dict]: 신호 정보 또는 None
            """
            # 현재 봉의 인덱스 찾기 (O(1) 딕셔너리 검색)
            bar_index = self.timestamp_to_index.get(bar.timestamp)
            
            if bar_index is None:
                logger.warning(f"봉을 찾을 수 없습니다: timestamp={bar.timestamp}")
                return None
            
            # 진입 조건 평가
            entry_def = self.definition.get("entry", {})
            
            # 롱 신호 체크
            long_signal = self._evaluate_entry_conditions(
                entry_def.get("long", {}),
                bar_index
            )
            
            # 숏 신호 체크
            short_signal = self._evaluate_entry_conditions(
                entry_def.get("short", {}),
                bar_index
            )
            
            # 동시 신호 발생 시 진입 안 함 (PRD 규칙)
            if long_signal and short_signal:
                logger.debug(f"동시 신호 발생으로 진입 스킵: bar_index={bar_index}")
                return None
            
            # 신호가 있으면 손절가 계산
            direction = None
            if long_signal:
                direction = "LONG"
            elif short_signal:
                direction = "SHORT"
            
            if direction:
                stop_loss = self._calculate_stop_loss(bar, direction, bar_index)
                if stop_loss is None:
                    logger.warning(f"손절가 계산 실패: bar_index={bar_index}")
                    return None
                
                return {
                    "direction": direction,
                    "stop_loss": stop_loss
                }
            
            return None
        
        return strategy_func
    
    def _evaluate_entry_conditions(
        self,
        entry_conditions: Dict[str, Any],
        bar_index: int
    ) -> bool:
        """
        진입 조건을 평가합니다.
        
        Args:
            entry_conditions: 진입 조건 정의 (예: {"and": [...]})
            bar_index: 현재 봉 인덱스
            
        Returns:
            bool: 조건 만족 여부
        """
        if not entry_conditions:
            return False
        
        # AND 조건 평가
        and_conditions = entry_conditions.get("and", [])
        if not and_conditions:
            return False
        
        for condition in and_conditions:
            if not self._evaluate_single_condition(condition, bar_index):
                return False
        
        return True
    
    def _evaluate_single_condition(
        self,
        condition: Dict[str, Any],
        bar_index: int
    ) -> bool:
        """
        단일 조건을 평가합니다.
        
        Args:
            condition: 조건 정의 (예: {"left": {...}, "op": "cross_above", "right": {...}})
            bar_index: 현재 봉 인덱스
            
        Returns:
            bool: 조건 만족 여부
        """
        left_def = condition.get("left", {})
        op = condition.get("op")
        right_def = condition.get("right", {})
        
        if not op:
            logger.warning(f"조건에 op가 없습니다: {condition}")
            return False
        
        # left, right 값 가져오기
        left_value = self._get_value(left_def, bar_index)
        right_value = self._get_value(right_def, bar_index)
        
        if left_value is None or right_value is None:
            return False
        
        # 연산자에 따라 평가
        if op == ">":
            return left_value > right_value
        elif op == "<":
            return left_value < right_value
        elif op == ">=":
            return left_value >= right_value
        elif op == "<=":
            return left_value <= right_value
        elif op == "==":
            return abs(left_value - right_value) < 1e-9  # float 비교
        elif op == "cross_above":
            return self._check_cross_above(left_def, right_def, bar_index)
        elif op == "cross_below":
            return self._check_cross_below(left_def, right_def, bar_index)
        else:
            logger.warning(f"지원하지 않는 연산자: {op}")
            return False
    
    def _parse_indicator_ref(self, ref: str) -> Tuple[str, str]:
        """
        지표 참조를 (DataFrame 컬럼명, 타임프레임) 튜플로 변환합니다.

        문법:
          - "ema_1.ema"         → ("ema_1_ema", "base")     (기존 동작)
          - "rsi_1h.rsi@1h"     → ("rsi_1h_rsi", "1h")      (MTF)
          - "ema_1@1d"          → ("ema_1", "1d")           (점 없이 @만)
          - "ema_1"             → ("ema_1", "base")

        @ 기호가 ref 내부에 이미 등장할 수 없다는 전제 (지표 ID는 영숫자+언더스코어).
        """
        # @ 접미사 분리 (있으면 HTF, 없으면 base)
        if "@" in ref:
            main_ref, tf = ref.rsplit("@", 1)
            tf = tf.strip()
        else:
            main_ref, tf = ref, BASE_TF

        # 점(.) → 언더스코어(_) 변환 (기존 규칙)
        if "." in main_ref:
            parts = main_ref.rsplit(".", 1)
            column_name = f"{parts[0]}_{parts[1]}"
        else:
            column_name = main_ref

        return column_name, tf

    def _resolve_tf_index(self, tf: str, base_index: int) -> Optional[int]:
        """base_index에서 TF별 유효 인덱스로 변환.

        Returns:
            - tf == "base": base_index 그대로
            - tf == HTF: 해당 base 시점에서 "이미 닫힌 마지막 HTF 봉 인덱스" (-1이면 None 반환)
            - 등록되지 않은 TF: None
        """
        if tf == BASE_TF:
            return base_index
        mapping = self.htf_index_maps.get(tf)
        if mapping is None:
            return None
        if base_index < 0 or base_index >= len(mapping):
            return None
        htf_idx = mapping[base_index]
        if htf_idx < 0:
            return None
        return htf_idx

    def _get_value(self, value_def: Dict[str, Any], bar_index: int) -> Optional[float]:
        """
        값 정의에서 실제 값을 가져옵니다.

        Args:
            value_def: 값 정의 (예: {"ref": "ema_1.ema"} 또는 {"value": 50})
            bar_index: 베이스 TF의 봉 인덱스

        Returns:
            Optional[float]: 값 또는 None
        """
        # ref가 있으면 지표 참조
        if "ref" in value_def:
            ref = value_def["ref"]
            column_name, tf = self._parse_indicator_ref(ref)

            calc = self.indicator_calcs.get(tf)
            if calc is None:
                logger.warning(
                    f"지표 참조 '{ref}' — 타임프레임 '{tf}' 데이터가 없습니다. "
                    f"사용 가능: {list(self.indicator_calcs.keys())}"
                )
                return None

            tf_index = self._resolve_tf_index(tf, bar_index)
            if tf_index is None:
                # HTF가 아직 한 봉도 닫히지 않음 → 값 없음
                logger.debug(
                    f"[HTF] ref='{ref}' tf='{tf}' base_index={bar_index}: "
                    f"닫힌 HTF 봉 없음 → None"
                )
                return None

            try:
                value = calc.get_value(column_name, tf_index)
                logger.debug(
                    f"[지표 값] ref='{ref}' column='{column_name}' tf='{tf}' "
                    f"tf_index={tf_index} value={value}"
                )
                return value
            except ValueError as e:
                available = [
                    col for col in calc.df.columns
                    if col not in ['open', 'high', 'low', 'close', 'volume', 'direction']
                ]
                logger.warning(
                    f"지표 값 가져오기 실패: ref='{ref}' column='{column_name}' tf='{tf}'\n"
                    f"  에러: {e}\n  사용 가능 컬럼({tf}): {available}"
                )
                return None

        # value가 있으면 상수 값
        elif "value" in value_def:
            return float(value_def["value"])

        # price 필드 참조 (예: {"price": "close"}) — 항상 base TF 사용
        elif "price" in value_def:
            price_field = value_def["price"]
            bar = self.bars[bar_index]

            if price_field == "open":
                return bar.open
            elif price_field == "high":
                return bar.high
            elif price_field == "low":
                return bar.low
            elif price_field == "close":
                return bar.close
            elif price_field == "volume":
                return bar.volume
            else:
                logger.warning(f"지원하지 않는 가격 필드: {price_field}")
                return None

        logger.warning(f"값 정의를 해석할 수 없습니다: {value_def}")
        return None
    
    def _check_cross_above(
        self,
        left_def: Dict[str, Any],
        right_def: Dict[str, Any],
        bar_index: int
    ) -> bool:
        """
        Cross Above 조건을 체크합니다.
        (이전 봉: left <= right, 현재 봉: left > right)
        
        Args:
            left_def: 왼쪽 값 정의
            right_def: 오른쪽 값 정의
            bar_index: 현재 봉 인덱스
            
        Returns:
            bool: Cross Above 발생 여부
        """
        # 첫 번째 봉에서는 cross 판정 불가
        if bar_index == 0:
            return False
        
        # 현재 값
        left_curr = self._get_value(left_def, bar_index)
        right_curr = self._get_value(right_def, bar_index)
        
        # 이전 값
        left_prev = self._get_value(left_def, bar_index - 1)
        right_prev = self._get_value(right_def, bar_index - 1)
        
        if any(v is None for v in [left_curr, right_curr, left_prev, right_prev]):
            return False
        
        # Cross Above: 이전에는 아래, 현재는 위
        return left_prev <= right_prev and left_curr > right_curr
    
    def _check_cross_below(
        self,
        left_def: Dict[str, Any],
        right_def: Dict[str, Any],
        bar_index: int
    ) -> bool:
        """
        Cross Below 조건을 체크합니다.
        (이전 봉: left >= right, 현재 봉: left < right)
        
        Args:
            left_def: 왼쪽 값 정의
            right_def: 오른쪽 값 정의
            bar_index: 현재 봉 인덱스
            
        Returns:
            bool: Cross Below 발생 여부
        """
        # 첫 번째 봉에서는 cross 판정 불가
        if bar_index == 0:
            return False
        
        # 현재 값
        left_curr = self._get_value(left_def, bar_index)
        right_curr = self._get_value(right_def, bar_index)
        
        # 이전 값
        left_prev = self._get_value(left_def, bar_index - 1)
        right_prev = self._get_value(right_def, bar_index - 1)
        
        if any(v is None for v in [left_curr, right_curr, left_prev, right_prev]):
            return False
        
        # Cross Below: 이전에는 위, 현재는 아래
        return left_prev >= right_prev and left_curr < right_curr
    
    def _calculate_stop_loss(
        self,
        bar: Bar,
        direction: str,
        bar_index: int
    ) -> Optional[float]:
        """
        손절가를 계산합니다.
        
        Args:
            bar: 현재 봉
            direction: 포지션 방향 (LONG/SHORT)
            bar_index: 봉 인덱스
            
        Returns:
            Optional[float]: 손절가 또는 None
        """
        stop_loss_def = self.definition.get("stop_loss", {})
        sl_type = stop_loss_def.get("type")
        
        if sl_type == "fixed_percent":
            percent = stop_loss_def.get("percent", 2.0)
            
            # 진입가는 close
            entry_price = bar.close
            
            if direction == "LONG":
                # 롱: 진입가 - (진입가 * percent / 100)
                stop_loss = entry_price * (1 - percent / 100)
            else:  # SHORT
                # 숏: 진입가 + (진입가 * percent / 100)
                stop_loss = entry_price * (1 + percent / 100)
            
            return stop_loss
        
        elif sl_type == "fixed_points":
            points = stop_loss_def.get("points", 100)
            entry_price = bar.close
            
            if direction == "LONG":
                stop_loss = entry_price - points
            else:  # SHORT
                stop_loss = entry_price + points
            
            return stop_loss
        
        elif sl_type == "atr_based":
            # ATR 기반 손절가 계산
            atr_indicator_id = stop_loss_def.get("atr_indicator_id")
            multiplier = stop_loss_def.get("multiplier", 2.0)
            
            if not atr_indicator_id:
                logger.error("ATR 기반 손절에는 atr_indicator_id가 필요합니다")
                return None
            
            # ATR 값 가져오기
            try:
                atr_value = self.indicator_calc.get_value(atr_indicator_id, bar_index)
            except ValueError as e:
                logger.error(f"ATR 지표 값을 가져올 수 없습니다: {e}")
                return None
            
            # ATR 값이 0이면 손절가 계산 불가
            if atr_value <= 0:
                logger.warning(f"ATR 값이 0 이하입니다: {atr_value}, 진입 스킵")
                return None
            
            # 진입가
            entry_price = bar.close
            
            if direction == "LONG":
                # 롱: 진입가 - (ATR * multiplier)
                stop_loss = entry_price - (atr_value * multiplier)
            else:  # SHORT
                # 숏: 진입가 + (ATR * multiplier)
                stop_loss = entry_price + (atr_value * multiplier)
            
            return stop_loss
        
        elif sl_type == "indicator_level":
            # 사용자 지표 기반 손절가 계산 (가격 레벨)
            # 지표 값 자체가 손절가가 됨
            long_ref = stop_loss_def.get("long_ref")
            short_ref = stop_loss_def.get("short_ref")
            
            # 방향에 따라 참조 선택
            ref = long_ref if direction == "LONG" else short_ref
            
            if not ref:
                logger.error(f"indicator_level 손절에 {direction} 참조가 없습니다")
                return None
            
            # _get_value 재사용 — @tf 접미사와 HTF 매핑을 일관되게 처리
            stop_loss_value = self._get_value({"ref": ref}, bar_index)
            if stop_loss_value is None:
                logger.warning(f"손절 지표 값을 가져올 수 없습니다 (ref={ref})")
                return None
            
            # 방어 로직: 유효하지 않은 값 처리
            import math
            if stop_loss_value is None or math.isnan(stop_loss_value) or math.isinf(stop_loss_value):
                logger.warning(f"손절 지표 값이 유효하지 않습니다 (ref={ref}): {stop_loss_value}, 진입 스킵")
                return None
            
            if stop_loss_value <= 0:
                logger.warning(f"손절가가 0 이하입니다 (ref={ref}): {stop_loss_value}, 진입 스킵")
                return None
            
            # 방향과 손절가 관계 검증
            entry_price = bar.close
            
            if direction == "LONG" and stop_loss_value >= entry_price:
                # LONG인데 손절가가 진입가 이상이면 리스크 0 또는 음수
                logger.warning(
                    f"LONG 손절가({stop_loss_value:.4f})가 진입가({entry_price:.4f}) 이상입니다, 진입 스킵"
                )
                return None
            
            if direction == "SHORT" and stop_loss_value <= entry_price:
                # SHORT인데 손절가가 진입가 이하이면 리스크 0 또는 음수
                logger.warning(
                    f"SHORT 손절가({stop_loss_value:.4f})가 진입가({entry_price:.4f}) 이하입니다, 진입 스킵"
                )
                return None
            
            return stop_loss_value
        
        else:
            logger.error(f"지원하지 않는 손절 타입: {sl_type}")
            return None
    
    def has_exit_conditions(self) -> bool:
        """
        전략에 진출 조건이 정의되어 있는지 확인합니다.
        
        Returns:
            bool: 진출 조건이 있으면 True
        """
        exit_def = self.definition.get("exit", {})
        if not exit_def:
            return False
        
        # 지표 기반 진출 조건 확인
        indicator_based = exit_def.get("indicator_based", {})
        if indicator_based.get("enabled", False):
            return True
        
        # ATR Trailing 확인
        atr_trailing = exit_def.get("atr_trailing", {})
        if atr_trailing.get("enabled", False):
            return True
        
        return False
    
    def has_indicator_based_exit(self) -> bool:
        """
        지표 기반 진출 조건이 활성화되어 있는지 확인합니다.
        """
        exit_def = self.definition.get("exit", {})
        indicator_based = exit_def.get("indicator_based", {})
        return indicator_based.get("enabled", False)
    
    def has_atr_trailing(self) -> bool:
        """
        ATR Trailing Stop이 활성화되어 있는지 확인합니다.
        """
        exit_def = self.definition.get("exit", {})
        atr_trailing = exit_def.get("atr_trailing", {})
        return atr_trailing.get("enabled", False)
    
    def get_atr_trailing_config(self) -> Optional[Dict[str, Any]]:
        """
        ATR Trailing Stop 설정을 반환합니다.
        
        Returns:
            Dict: {'atr_indicator_id': str, 'multiplier': float} 또는 None
        """
        exit_def = self.definition.get("exit", {})
        atr_trailing = exit_def.get("atr_trailing", {})
        
        if not atr_trailing.get("enabled", False):
            return None
        
        return {
            "atr_indicator_id": atr_trailing.get("atr_indicator_id", ""),
            "multiplier": atr_trailing.get("multiplier", 2.0)
        }
    
    def evaluate_exit_condition(self, bar_index: int, direction: str) -> bool:
        """
        지표 기반 진출 조건을 평가합니다.
        
        Args:
            bar_index: 현재 봉 인덱스
            direction: 포지션 방향 ('LONG' 또는 'SHORT')
        
        Returns:
            bool: 진출 조건 충족 여부
        """
        exit_def = self.definition.get("exit", {})
        indicator_based = exit_def.get("indicator_based", {})
        
        if not indicator_based.get("enabled", False):
            return False
        
        # 방향에 따라 조건 선택
        if direction == "LONG":
            conditions = indicator_based.get("long", {})
        else:  # SHORT
            conditions = indicator_based.get("short", {})
        
        return self._evaluate_entry_conditions(conditions, bar_index)
    
    def get_atr_value(self, bar_index: int) -> Optional[float]:
        """
        ATR Trailing용 ATR 값을 가져옵니다.
        
        Args:
            bar_index: 현재 봉 인덱스
        
        Returns:
            Optional[float]: ATR 값 또는 None
        """
        config = self.get_atr_trailing_config()
        if not config:
            return None
        
        atr_indicator_id = config.get("atr_indicator_id", "")
        if not atr_indicator_id:
            return None
        
        try:
            return self.indicator_calc.get_value(atr_indicator_id, bar_index)
        except ValueError as e:
            logger.warning(f"ATR 지표 값을 가져올 수 없습니다: {e}")
            return None
    
    def create_exit_checker(self) -> Callable[[int, str], bool]:
        """
        백테스트 엔진이 사용할 진출 조건 체커 함수를 생성합니다.
        
        Returns:
            Callable: exit_checker(bar_index, direction) -> bool
                - True: 진출 조건 충족 (포지션 청산)
                - False: 진출 조건 미충족
        """
        def exit_checker(bar_index: int, direction: str) -> bool:
            """
            지표 기반 진출 조건을 체크합니다.
            
            Args:
                bar_index: 현재 봉 인덱스
                direction: 포지션 방향 ('LONG' 또는 'SHORT')
            
            Returns:
                bool: 진출 조건 충족 여부
            """
            return self.evaluate_exit_condition(bar_index, direction)
        
        return exit_checker

