"""
전략 파서(Strategy Parser) 모듈

Strategy JSON을 파싱하여 신호를 생성합니다.
"""

from typing import Dict, Any, List, Optional, Callable
import pandas as pd
from ..models.bar import Bar
from .indicators import IndicatorCalculator
import logging

logger = logging.getLogger(__name__)


class StrategyParser:
    """
    전략 파서
    
    Strategy JSON을 파싱하여 봉마다 진입 신호를 생성합니다.
    """
    
    def __init__(self, strategy_definition: Dict[str, Any], bars: List[Bar], df: pd.DataFrame):
        """
        Args:
            strategy_definition: 전략 정의 JSON
            bars: 봉 데이터 리스트
            df: OHLCV DataFrame (지표 계산용)
        """
        self.definition = strategy_definition
        self.bars = bars
        self.df = df
        
        # timestamp -> index 매핑 생성 (O(1) 검색을 위해)
        # 매 봉마다 O(n) 순차 검색을 하면 전체 O(n²)이 되므로 미리 딕셔너리로 생성
        self.timestamp_to_index = {bar.timestamp: i for i, bar in enumerate(bars)}
        
        # Indicator Calculator 초기화 (DataFrame 전달)
        self.indicator_calc = IndicatorCalculator(df)
        
        # 커스텀 지표 동적 로드
        self._load_custom_indicators()
        
        # 지표 계산
        self._calculate_indicators()
        
        # 이전 지표 값 (cross 판정용)
        self.prev_indicator_values: Dict[str, float] = {}
    
    def _load_custom_indicators(self) -> None:
        """
        데이터베이스에서 커스텀 지표를 로드하여 등록
        
        Note:
            DB 파일이 없거나 로드 실패 시에도 백테스트는 계속 진행됩니다.
            내장 지표만으로도 동작 가능하기 때문입니다.
        """
        from pathlib import Path
        from .indicator_loader import register_custom_indicators
        
        db_path = Path("db/algoforge.db")
        
        if not db_path.exists():
            logger.debug(f"데이터베이스 파일이 없습니다: {db_path}")
            return
        
        try:
            count = register_custom_indicators(self.indicator_calc, str(db_path))
            logger.debug(f"커스텀 지표 {count}개 로드 완료")
        except Exception as e:
            logger.warning(f"커스텀 지표 로드 실패: {e}")
    
    def _calculate_indicators(self) -> None:
        """
        전략에 정의된 모든 지표를 사전 계산합니다.
        
        새로운 DataFrame 기반 IndicatorCalculator를 사용하여
        모든 지표를 한 번에 계산하고 DataFrame에 컬럼으로 저장합니다.
        """
        indicators = self.definition.get("indicators", [])
        
        logger.info(f"[전략 파싱] 지표 계산 시작: {len(indicators)}개")
        
        for indicator in indicators:
            if not indicator.get("id") or not indicator.get("type"):
                logger.warning(f"지표 정의가 불완전합니다: {indicator}")
                continue
            
            logger.info(f"[전략 파싱] 지표 계산 중: id={indicator.get('id')}, type={indicator.get('type')}")
            
            # 새로운 API 사용: calculate_indicator()
            try:
                self.indicator_calc.calculate_indicator(indicator)
            except Exception as e:
                logger.error(f"지표 계산 실패: {indicator.get('id')}, {e}", exc_info=True)
        
        # 계산 완료 후 DataFrame 컬럼 목록 출력
        indicator_columns = [col for col in self.df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        logger.info(f"[전략 파싱] 지표 계산 완료. 생성된 컬럼: {indicator_columns}")
    
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
    
    def _parse_indicator_ref(self, ref: str) -> str:
        """
        지표 참조를 DataFrame 컬럼명으로 변환합니다.
        
        프론트엔드에서는 점(.)으로 구분된 참조를 사용하지만,
        백엔드 DataFrame 컬럼명은 언더스코어(_)로 구분됩니다.
        
        Args:
            ref: 지표 참조 (예: "ema_1.ema", "cvol_1.vmf")
            
        Returns:
            str: DataFrame 컬럼명 (예: "ema_1_ema", "cvol_1_vmf")
            
        Examples:
            >>> _parse_indicator_ref("ema_1.ema")
            "ema_1_ema"
            >>> _parse_indicator_ref("cvol_1.vmf")
            "cvol_1_vmf"
            >>> _parse_indicator_ref("ema_1")  # 점이 없으면 그대로
            "ema_1"
        """
        # 점이 없으면 그대로 반환 (하위 호환성)
        if "." not in ref:
            return ref
        
        # 마지막 점을 언더스코어로 변환
        # "cvol_1.vmf" → "cvol_1_vmf"
        parts = ref.rsplit(".", 1)  # 오른쪽부터 1개만 split
        return f"{parts[0]}_{parts[1]}"
    
    def _get_value(self, value_def: Dict[str, Any], bar_index: int) -> Optional[float]:
        """
        값 정의에서 실제 값을 가져옵니다.
        
        Args:
            value_def: 값 정의 (예: {"ref": "ema_1.ema"} 또는 {"value": 50})
            bar_index: 봉 인덱스
            
        Returns:
            Optional[float]: 값 또는 None
        """
        # ref가 있으면 지표 참조
        if "ref" in value_def:
            ref = value_def["ref"]
            
            # 점(.)으로 구분된 참조를 언더스코어(_)로 변환
            # 예: "cvol_1.vmf" → "cvol_1_vmf"
            # 예: "ema_1.ema" → "ema_1_ema" 또는 "ema_1" (마지막 부분이 'main'이면 제거)
            column_name = self._parse_indicator_ref(ref)
            
            # logger.info(f"[지표 참조] ref='{ref}' → column='{column_name}'")
            
            # 지표 참조인 경우
            try:
                value = self.indicator_calc.get_value(column_name, bar_index)
                logger.debug(f"[지표 값] column='{column_name}', bar_index={bar_index}, value={value}")
                return value
            except ValueError as e:
                # 사용 가능한 컬럼 목록 출력
                available_columns = [col for col in self.df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
                logger.warning(
                    f"지표 값 가져오기 실패: {ref} (컬럼: {column_name})\n"
                    f"  에러: {e}\n"
                    f"  사용 가능한 지표 컬럼: {available_columns}"
                )
                return None
        
        # value가 있으면 상수 값
        elif "value" in value_def:
            return float(value_def["value"])
        
        # price 필드 참조 (예: {"price": "close"})
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
        
        else:
            logger.error(f"지원하지 않는 손절 타입: {sl_type}")
            return None

