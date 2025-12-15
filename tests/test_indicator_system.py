"""
지표 관리 시스템 테스트

1. 커스텀 지표 다중 리턴값 지원
2. 코드 검증기
3. 동적 로더
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from engine.utils.indicators import IndicatorCalculator
from apps.api.utils.code_validator import (
    validate_indicator_code,
    validate_indicator_code_simple,
    extract_function_name
)


class TestIndicatorMultipleReturns:
    """커스텀 지표 다중 리턴값 테스트"""
    
    def test_single_return_value(self):
        """단일 리턴값 (기존 방식) 테스트"""
        # 테스트 데이터 생성
        df = pd.DataFrame({
            'timestamp': range(100),
            'open': np.random.randn(100) + 100,
            'high': np.random.randn(100) + 101,
            'low': np.random.randn(100) + 99,
            'close': np.random.randn(100) + 100,
            'volume': np.random.randint(1000, 10000, 100),
            'direction': [1] * 100
        })
        
        # IndicatorCalculator 생성
        calc = IndicatorCalculator(df)
        
        # 커스텀 지표 함수 정의 (단일 리턴)
        def custom_sma(df, params):
            period = params.get('period', 20)
            return df['close'].rolling(window=period).mean()
        
        # 등록 및 계산
        calc.register_custom_indicator('custom_sma', custom_sma)
        calc.calculate_indicator({
            'id': 'sma_20',
            'type': 'custom_sma',
            'params': {'period': 20}
        })
        
        # 검증
        assert 'sma_20' in calc.df.columns
        assert len(calc.df['sma_20']) == 100
        assert not calc.df['sma_20'].isna().all()
    
    def test_multiple_return_values(self):
        """다중 리턴값 테스트 (Dict[str, pd.Series])"""
        # 테스트 데이터 생성
        df = pd.DataFrame({
            'timestamp': range(100),
            'open': np.random.randn(100) + 100,
            'high': np.random.randn(100) + 101,
            'low': np.random.randn(100) + 99,
            'close': np.random.randn(100) + 100,
            'volume': np.random.randint(1000, 10000, 100),
            'direction': [1] * 100
        })
        
        # IndicatorCalculator 생성
        calc = IndicatorCalculator(df)
        
        # 커스텀 지표 함수 정의 (다중 리턴)
        def custom_bollinger(df, params):
            period = params.get('period', 20)
            std_dev = params.get('std_dev', 2.0)
            
            sma = df['close'].rolling(window=period).mean()
            std = df['close'].rolling(window=period).std()
            
            return {
                'main': sma,
                'upper': sma + (std * std_dev),
                'lower': sma - (std * std_dev)
            }
        
        # 등록 및 계산
        calc.register_custom_indicator('custom_bollinger', custom_bollinger)
        calc.calculate_indicator({
            'id': 'bb',
            'type': 'custom_bollinger',
            'params': {'period': 20, 'std_dev': 2.0}
        })
        
        # 검증: main은 bb, 나머지는 bb_upper, bb_lower
        assert 'bb' in calc.df.columns  # main
        assert 'bb_upper' in calc.df.columns
        assert 'bb_lower' in calc.df.columns
        
        # 값 검증
        assert len(calc.df['bb']) == 100
        assert not calc.df['bb'].isna().all()
        
        # NaN이 아닌 값들만 비교
        valid_mask = ~calc.df['bb'].isna()
        assert (calc.df.loc[valid_mask, 'bb_upper'] >= calc.df.loc[valid_mask, 'bb']).all()
        assert (calc.df.loc[valid_mask, 'bb_lower'] <= calc.df.loc[valid_mask, 'bb']).all()
    
    def test_invalid_return_type(self):
        """잘못된 리턴 타입 테스트"""
        df = pd.DataFrame({
            'timestamp': range(100),
            'close': np.random.randn(100) + 100,
        })
        
        calc = IndicatorCalculator(df)
        
        # 잘못된 리턴 타입 (list)
        def bad_indicator(df, params):
            return [1, 2, 3]
        
        calc.register_custom_indicator('bad_indicator', bad_indicator)
        
        with pytest.raises(ValueError, match="pd.Series 또는 Dict"):
            calc.calculate_indicator({
                'id': 'bad',
                'type': 'bad_indicator',
                'params': {}
            })


class TestCodeValidator:
    """코드 검증기 테스트"""
    
    def test_valid_code(self):
        """유효한 코드 검증"""
        code = """
def calculate_custom_sma(df, params):
    period = params.get('period', 20)
    return df['close'].rolling(window=period).mean()
"""
        
        is_valid, message, errors = validate_indicator_code(code)
        
        assert is_valid is True
        assert message == "코드 검증 통과"
        assert errors == []
    
    def test_dangerous_keyword(self):
        """위험 키워드 검증"""
        code = """
def bad_function(df, params):
    import os
    os.system('rm -rf /')
    return df['close']
"""
        
        is_valid, message, errors = validate_indicator_code(code)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any('import os' in err for err in errors)
    
    def test_syntax_error(self):
        """구문 오류 검증"""
        code = """
def bad_syntax(df, params)
    return df['close'
"""
        
        is_valid, message, errors = validate_indicator_code(code)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any('구문 오류' in err for err in errors)
    
    def test_wrong_argument_count(self):
        """잘못된 인자 개수 검증"""
        code = """
def wrong_args(df):
    return df['close']
"""
        
        is_valid, message, errors = validate_indicator_code(code)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any('2개의 인자' in err for err in errors)
    
    def test_extract_function_name(self):
        """함수 이름 추출 테스트"""
        code = """
def my_custom_indicator(df, params):
    return df['close']
"""
        
        func_name = extract_function_name(code)
        assert func_name == "my_custom_indicator"


class TestIndicatorLoader:
    """동적 로더 테스트"""
    
    def test_load_from_database(self):
        """데이터베이스에서 커스텀 지표 로드 테스트"""
        from engine.utils.indicator_loader import load_custom_indicators_from_db
        
        db_path = Path("db/algoforge.db")
        
        if not db_path.exists():
            pytest.skip("데이터베이스 파일이 없습니다")
        
        # 로드
        indicators = load_custom_indicators_from_db(str(db_path))
        
        # 검증 (딕셔너리 형태로 반환되어야 함)
        assert isinstance(indicators, dict)
        
        # 각 지표가 callable인지 확인
        for name, func in indicators.items():
            assert callable(func)
            print(f"로드된 지표: {name}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

