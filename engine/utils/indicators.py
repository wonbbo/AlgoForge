"""
지표(Indicator) 계산 모듈 - DataFrame 기반

pandas DataFrame과 ta 라이브러리를 활용하여 기술적 지표를 계산합니다.
모든 계산은 결정적(deterministic)이어야 합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Callable
import logging

# ta 라이브러리 import
from ta.trend import EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    DataFrame 기반 지표 계산기
    
    pandas DataFrame과 ta 라이브러리를 활용하여 기술적 지표를 계산합니다.
    전체 데이터에 대해 한 번에 지표를 계산하고, 결과를 DataFrame 컬럼으로 저장합니다.
    
    특징:
    - 벡터화 연산으로 성능 향상
    - ta 라이브러리 활용으로 코드 간결화
    - 커스텀 지표 등록 가능
    - 결정적 결과 보장
    """
    
    def __init__(self, df: pd.DataFrame | list):
        """
        Args:
            df: OHLCV DataFrame (columns: timestamp, open, high, low, close, volume, direction)
        
        Note:
            원본 DataFrame은 보호하기 위해 복사본을 생성합니다.
        """
        # df가 리스트 형태로 들어오는 경우 DataFrame으로 변환
        if df is None:
            raise ValueError("지표 계산을 위한 DataFrame이 필요합니다")
        
        if isinstance(df, list):
            if len(df) > 0 and hasattr(df[0], "__dict__"):
                # Bar 객체 리스트인 경우 필드 추출
                self.df = pd.DataFrame([b.__dict__ for b in df]).copy()
            else:
                self.df = pd.DataFrame(df).copy()
        else:
            self.df = df.copy()
        
        # 필수 컬럼 채우기 (close는 반드시 필요, 나머지는 없는 경우 기본값 사용)
        if 'close' not in self.df.columns:
            raise ValueError("지표 계산에 필요한 'close' 컬럼이 없습니다")
        
        defaults = {
            'open': self.df['close'],
            'high': self.df['close'],
            'low': self.df['close'],
            'volume': 0.0,
            'direction': 0
        }
        for col, default_val in defaults.items():
            if col not in self.df.columns:
                self.df[col] = default_val
        
        # 커스텀 지표 함수 저장소
        self.custom_indicators: Dict[str, Callable] = {}
    
    def calculate_indicator(self, indicator_def: Dict[str, Any]) -> None:
        """
        지표 정의에 따라 계산하고 DataFrame에 컬럼 추가
        
        Args:
            indicator_def: 지표 정의 딕셔너리
                - id: 지표 ID (컬럼명으로 사용)
                - type: 지표 타입 (ema, sma, rsi, atr 등)
                - params: 파라미터 딕셔너리
        
        Raises:
            ValueError: 지원하지 않는 지표 타입이거나 파라미터가 잘못된 경우
        """
        indicator_id = indicator_def.get("id")
        indicator_type = indicator_def.get("type")
        params = indicator_def.get("params", {})
        
        if not indicator_id:
            raise ValueError("indicator_id가 필요합니다")
        
        if not indicator_type:
            raise ValueError("indicator_type이 필요합니다")
        
        # 지표 타입에 따라 계산
        try:
            if indicator_type == "ema":
                self._calculate_ema(indicator_id, params)
            elif indicator_type == "sma":
                self._calculate_sma(indicator_id, params)
            elif indicator_type == "rsi":
                self._calculate_rsi(indicator_id, params)
            elif indicator_type == "atr":
                self._calculate_atr(indicator_id, params)
            elif indicator_type in self.custom_indicators:
                # 커스텀 지표
                self._calculate_custom(indicator_id, indicator_type, params)
            else:
                raise ValueError(f"지원하지 않는 지표 타입: {indicator_type}")
                
        except Exception as e:
            logger.error(f"지표 계산 실패: {indicator_id}, {e}", exc_info=True)
            raise
    
    def get_value(self, indicator_id: str, bar_index: int) -> float:
        """
        특정 봉에서 지표 값을 반환
        
        Args:
            indicator_id: 지표 ID (컬럼명)
            bar_index: 봉 인덱스 (0부터 시작)
        
        Returns:
            float: 지표 값
        
        Raises:
            ValueError: 지표가 없거나 인덱스가 범위를 벗어난 경우
        """
        if indicator_id not in self.df.columns:
            raise ValueError(f"지표 '{indicator_id}'가 계산되지 않았습니다")
        
        if bar_index < 0 or bar_index >= len(self.df):
            raise ValueError(f"bar_index {bar_index}가 범위를 벗어났습니다")
        
        # iloc를 사용하여 인덱스 기반 접근 (빠름)
        value = self.df.iloc[bar_index][indicator_id]
        
        # NaN 처리 (초기 데이터 부족 시)
        if pd.isna(value):
            # 첫 번째 유효한 값으로 대체 (백워드 필)
            first_valid = self.df[indicator_id].first_valid_index()
            if first_valid is not None:
                return self.df.loc[first_valid, indicator_id]
            else:
                # 모든 값이 NaN이면 0 반환
                return 0.0
        
        return float(value)
    
    def register_custom_indicator(
        self, 
        name: str, 
        func: Callable[[pd.DataFrame, Dict[str, Any]], Any]
    ) -> None:
        """
        커스텀 지표 함수 등록
        
        Args:
            name: 지표 타입 이름
            func: 지표 계산 함수
                입력: (df: DataFrame, params: Dict)
                출력: pd.Series 또는 Dict[str, pd.Series]
        
        Examples:
            # 단일 값 반환
            def custom_vwap(df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
                typical_price = (df['high'] + df['low'] + df['close']) / 3
                return (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
            
            calculator.register_custom_indicator('vwap', custom_vwap)
            
            # 여러 값 반환
            def custom_macd(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, pd.Series]:
                # ... MACD 계산 ...
                return {
                    'main': macd_line,
                    'signal': signal_line,
                    'histogram': histogram
                }
            
            calculator.register_custom_indicator('custom_macd', custom_macd)
        """
        self.custom_indicators[name] = func
        logger.info(f"커스텀 지표 등록: {name}")
    
    def _calculate_ema(self, indicator_id: str, params: Dict[str, Any]) -> None:
        """
        EMA (Exponential Moving Average) 계산 - ta 라이브러리 사용
        
        Args:
            indicator_id: 지표 ID
            params: 파라미터
                - source: 소스 필드 (open, high, low, close, volume) - 기본: close
                - period: 기간 - 기본: 20
        """
        source = params.get("source", "close")
        period = params.get("period", 20)
        
        if period <= 0:
            raise ValueError(f"period는 0보다 커야 합니다: {period}")
        
        if source not in self.df.columns:
            raise ValueError(f"소스 필드가 없습니다: {source}")
        
        # ta 라이브러리 사용
        ema_indicator = EMAIndicator(close=self.df[source], window=period, fillna=True)
        self.df[indicator_id] = ema_indicator.ema_indicator().bfill()
    
    def _calculate_sma(self, indicator_id: str, params: Dict[str, Any]) -> None:
        """
        SMA (Simple Moving Average) 계산 - ta 라이브러리 사용
        
        Args:
            indicator_id: 지표 ID
            params: 파라미터
                - source: 소스 필드 - 기본: close
                - period: 기간 - 기본: 20
        """
        source = params.get("source", "close")
        period = params.get("period", 20)
        
        if period <= 0:
            raise ValueError(f"period는 0보다 커야 합니다: {period}")
        
        if source not in self.df.columns:
            raise ValueError(f"소스 필드가 없습니다: {source}")
        
        # ta 라이브러리 사용
        sma_indicator = SMAIndicator(close=self.df[source], window=period, fillna=True)
        self.df[indicator_id] = sma_indicator.sma_indicator().bfill()
    
    def _calculate_rsi(self, indicator_id: str, params: Dict[str, Any]) -> None:
        """
        RSI (Relative Strength Index) 계산 - ta 라이브러리 사용
        
        Args:
            indicator_id: 지표 ID
            params: 파라미터
                - source: 소스 필드 - 기본: close
                - period: 기간 - 기본: 14
        """
        source = params.get("source", "close")
        period = params.get("period", 14)
        
        if period <= 0:
            raise ValueError(f"period는 0보다 커야 합니다: {period}")
        
        if source not in self.df.columns:
            raise ValueError(f"소스 필드가 없습니다: {source}")
        
        # ta 라이브러리 사용
        rsi_indicator = RSIIndicator(close=self.df[source], window=period, fillna=True)
        self.df[indicator_id] = rsi_indicator.rsi().bfill()
    
    def _calculate_atr(self, indicator_id: str, params: Dict[str, Any]) -> None:
        """
        ATR (Average True Range) 계산 - ta 라이브러리 사용
        
        Args:
            indicator_id: 지표 ID
            params: 파라미터
                - period: 기간 - 기본: 14
        
        Note:
            ATR은 high, low, close 세 개의 컬럼을 사용합니다.
            데이터가 period보다 작으면 사용 가능한 데이터로 계산합니다.
        """
        period = params.get("period", 14)
        
        if period <= 0:
            raise ValueError(f"period는 0보다 커야 합니다: {period}")
        
        # 필수 컬럼 확인
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"ATR 계산에 필요한 컬럼이 없습니다: {col}")
        
        # True Range 계산
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 단순 이동평균 기반 ATR (테스트 기대치와 일치)
        atr = true_range.rolling(window=period, min_periods=1).mean()
        self.df[indicator_id] = atr.bfill()
    
    def calculate_atr(self, indicator_id: str, period: int = 14) -> None:
        """
        공개용 ATR 계산 래퍼 (테스트 호환성)
        
        Args:
            indicator_id: 저장할 지표 ID
            period: ATR 기간 (기본 14)
        """
        self._calculate_atr(indicator_id, {"period": period})
    
    def _calculate_custom(
        self, 
        indicator_id: str, 
        indicator_type: str, 
        params: Dict[str, Any]
    ) -> None:
        """
        커스텀 지표 계산 - 단일 또는 다중 리턴값 지원
        
        Args:
            indicator_id: 지표 ID
            indicator_type: 지표 타입 (등록된 커스텀 지표 이름)
            params: 파라미터
        
        Note:
            커스텀 함수는 다음 중 하나를 반환할 수 있습니다:
            - pd.Series: 단일 값 -> indicator_id에 저장
            - Dict[str, pd.Series]: 여러 값 -> indicator_id_key에 저장
              (단, key='main'이면 indicator_id에 저장)
            
            예시:
                지표 ID가 'macd_1'이고 반환값이 {'main': ..., 'signal': ..., 'histogram': ...}이면
                - 'macd_1' (main)
                - 'macd_1_signal'
                - 'macd_1_histogram'
                로 DataFrame에 저장됩니다.
        """
        if indicator_type not in self.custom_indicators:
            raise ValueError(f"등록되지 않은 커스텀 지표: {indicator_type}")
        
        # 커스텀 함수 호출
        func = self.custom_indicators[indicator_type]
        result = func(self.df, params)
        
        # 결과 타입에 따라 처리
        if isinstance(result, pd.Series):
            # 단일 Series: 기존 방식
            if len(result) != len(self.df):
                raise ValueError(
                    f"커스텀 지표 길이가 DataFrame과 다릅니다: "
                    f"expected {len(self.df)}, got {len(result)}"
                )
            
            self.df[indicator_id] = result
            logger.debug(f"커스텀 지표 저장 (단일): {indicator_id}")
            
        elif isinstance(result, dict):
            # 여러 Series: Dict[str, pd.Series] 형태
            if not result:
                raise ValueError("반환된 딕셔너리가 비어있습니다")
            
            for key, series in result.items():
                if not isinstance(series, pd.Series):
                    raise ValueError(
                        f"딕셔너리 값은 pd.Series여야 합니다: key={key}, type={type(series)}"
                    )
                
                if len(series) != len(self.df):
                    raise ValueError(
                        f"지표 길이가 DataFrame과 다릅니다: key={key}, "
                        f"expected {len(self.df)}, got {len(series)}"
                    )
                
                # 컬럼명 생성: main은 indicator_id, 나머지는 indicator_id_key
                column_name = indicator_id if key == "main" else f"{indicator_id}_{key}"
                self.df[column_name] = series
                logger.info(f"[커스텀 지표] 컬럼 생성: {column_name} (indicator_id={indicator_id}, key={key})")
                
        else:
            raise ValueError(
                f"커스텀 지표 함수는 pd.Series 또는 Dict[str, pd.Series]를 반환해야 합니다. "
                f"실제 반환 타입: {type(result)}"
            )
