"""
지표 동적 로더 - 데이터베이스에서 커스텀 지표 로드

백테스트 실행 시 데이터베이스에서 커스텀 지표를 읽어와
IndicatorCalculator에 등록합니다.
"""

import sqlite3
from typing import Callable, Dict, Any
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def load_custom_indicators_from_db(db_path: str) -> Dict[str, Callable]:
    """
    데이터베이스에서 커스텀 지표를 로드
    
    Args:
        db_path: SQLite 데이터베이스 경로
    
    Returns:
        Dict[str, Callable]: {indicator_type: calculate_function}
        
    Note:
        로드에 실패한 지표는 로그에 기록하고 건너뜁니다.
        전체 로드 실패를 방지하기 위함입니다.
    """
    indicators = {}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT type, code, name FROM indicators WHERE implementation_type = 'custom'"
        )
        
        for row in cursor.fetchall():
            indicator_type, code, name = row
            
            try:
                func = _create_function_from_code(code)
                indicators[indicator_type] = func
                logger.info(f"커스텀 지표 로드 성공: {indicator_type} ({name})")
            except Exception as e:
                logger.error(
                    f"커스텀 지표 로드 실패: {indicator_type} ({name}), "
                    f"에러: {str(e)}",
                    exc_info=True
                )
        
        conn.close()
        
    except Exception as e:
        logger.error(f"데이터베이스 접근 실패: {db_path}, 에러: {str(e)}")
    
    return indicators


def _create_function_from_code(code: str) -> Callable:
    """
    코드 문자열에서 함수 객체 생성
    
    Args:
        code: Python 함수 코드
    
    Returns:
        Callable: 지표 계산 함수
    
    Raises:
        ValueError: 함수를 찾을 수 없거나 실행 실패 시
    
    Warning:
        exec 사용은 보안 위험이 있으므로 반드시 코드 검증 필요!
        개인 사용 MVP이므로 기본 검증만 수행하지만,
        프로덕션 환경에서는 샌드박스 환경에서 실행 권장
    """
    # 안전한 네임스페이스 (허용된 라이브러리만)
    safe_namespace = {
        'pd': pd,
        'pandas': pd,
        'np': np,
        'numpy': np,
        'Dict': Dict,
        'Any': Any,
    }
    
    # ta 라이브러리 import 허용
    try:
        import ta
        safe_namespace['ta'] = ta
        
        # 자주 사용하는 ta 모듈도 추가
        from ta.momentum import RSIIndicator
        from ta.volatility import AverageTrueRange, BollingerBands
        from ta.trend import MACD, EMAIndicator, SMAIndicator, CCIIndicator

        safe_namespace['MACD'] = MACD
        safe_namespace['CCIIndicator'] = CCIIndicator
        safe_namespace['EMAIndicator'] = EMAIndicator
        safe_namespace['SMAIndicator'] = SMAIndicator
        safe_namespace['RSIIndicator'] = RSIIndicator
        safe_namespace['BollingerBands'] = BollingerBands
        safe_namespace['AverageTrueRange'] = AverageTrueRange
        
    except ImportError:
        logger.warning("ta 라이브러리를 찾을 수 없습니다")
    
    # 코드 실행
    try:
        exec(code, safe_namespace)
    except Exception as e:
        raise ValueError(f"코드 실행 실패: {str(e)}")
    
    # 함수 찾기 (첫 번째 callable 객체 반환)
    for name, obj in safe_namespace.items():
        # 내장 함수나 import된 모듈 제외
        if callable(obj) and not name.startswith('_') and name not in [
            'pd', 'pandas', 'np', 'numpy', 'Dict', 'Any', 'ta',
            'EMAIndicator', 'SMAIndicator', 'CCIIndicator', 'MACD', 'RSIIndicator',
            'AverageTrueRange', 'BollingerBands'
        ]:
            return obj
    
    raise ValueError("함수를 찾을 수 없습니다. 코드에 함수 정의가 있는지 확인하세요.")


def register_custom_indicators(indicator_calc, db_path: str) -> int:
    """
    커스텀 지표를 로드하여 IndicatorCalculator에 등록
    
    Args:
        indicator_calc: IndicatorCalculator 인스턴스
        db_path: SQLite 데이터베이스 경로
    
    Returns:
        int: 등록된 지표 개수
    """
    custom_indicators = load_custom_indicators_from_db(db_path)
    
    for name, func in custom_indicators.items():
        indicator_calc.register_custom_indicator(name, func)
    
    logger.info(f"커스텀 지표 {len(custom_indicators)}개 등록 완료")
    
    return len(custom_indicators)

