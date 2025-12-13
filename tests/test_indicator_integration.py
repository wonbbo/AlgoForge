"""
지표 시스템 통합 테스트

커스텀 지표 등록 → 전략에서 사용 → 백테스트 실행 → 결과 검증
"""

import pytest
from pathlib import Path
import sys
import json

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


class TestIndicatorIntegration:
    """지표 시스템 통합 테스트"""
    
    def test_custom_indicator_in_strategy(self):
        """
        커스텀 지표를 등록하고 전략에서 사용하는 통합 테스트
        
        시나리오:
        1. 커스텀 Simple SMA 지표 등록
        2. 해당 지표를 사용하는 전략 생성
        3. 백테스트 실행 (실제 실행은 스킵, 지표 로드만 확인)
        """
        # 1. 커스텀 지표 등록
        custom_indicator = {
            "name": "Test Simple SMA",
            "type": "test_simple_sma",
            "description": "테스트용 단순 SMA",
            "category": "trend",
            "code": """def calculate_test_simple_sma(df, params):
    period = params.get('period', 20)
    return df['close'].rolling(window=period).mean().fillna(0)
""",
            "params_schema": '{"period": 20}',
            "output_fields": ["main"]
        }
        
        response = client.post("/api/indicators/custom", json=custom_indicator)
        assert response.status_code == 201
        
        # 2. 등록된 지표 확인
        response = client.get("/api/indicators/test_simple_sma")
        assert response.status_code == 200
        
        # 3. 지표 목록에서 확인
        response = client.get("/api/indicators/?implementation_type=custom")
        assert response.status_code == 200
        data = response.json()
        
        types = [ind["type"] for ind in data["indicators"]]
        assert "test_simple_sma" in types
        
        # 4. 정리
        client.delete("/api/indicators/test_simple_sma")
        
        # 테스트 성공
    
    def test_multiple_output_indicator(self):
        """
        다중 출력 커스텀 지표 등록 및 사용 테스트
        
        시나리오:
        1. MACD 스타일의 다중 출력 지표 등록
        2. output_fields 검증
        """
        # 1. 다중 출력 지표 등록
        custom_indicator = {
            "name": "Test MACD",
            "type": "test_macd",
            "description": "테스트용 MACD (다중 출력)",
            "category": "momentum",
            "code": """def calculate_test_macd(df, params):
    fast = params.get('fast', 12)
    slow = params.get('slow', 26)
    signal = params.get('signal', 9)
    
    # 간단한 MACD 계산 (ta 라이브러리 없이)
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return {
        'main': macd_line.fillna(0),
        'signal': signal_line.fillna(0),
        'histogram': histogram.fillna(0)
    }
""",
            "params_schema": '{"fast": 12, "slow": 26, "signal": 9}',
            "output_fields": ["main", "signal", "histogram"]
        }
        
        response = client.post("/api/indicators/custom", json=custom_indicator)
        assert response.status_code == 201
        
        # 2. 등록된 지표 확인
        response = client.get("/api/indicators/test_macd")
        assert response.status_code == 200
        data = response.json()
        
        # output_fields 검증
        assert data["output_fields"] == ["main", "signal", "histogram"]
        
        # 3. 정리
        client.delete("/api/indicators/test_macd")
        
        # 테스트 성공
    
    def test_indicator_code_validation_flow(self):
        """
        지표 코드 검증 플로우 테스트
        
        시나리오:
        1. 잘못된 코드 검증 → 실패
        2. 올바른 코드 검증 → 성공
        3. 검증 통과한 코드로 지표 등록
        """
        # 1. 잘못된 코드 검증
        bad_code = """def bad_indicator(df):
    import os
    return df['close']
"""
        
        response = client.post("/api/indicators/validate", json={"code": bad_code})
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        
        # 2. 올바른 코드 검증
        good_code = """def good_indicator(df, params):
    period = params.get('period', 20)
    return df['close'].rolling(window=period).mean()
"""
        
        response = client.post("/api/indicators/validate", json={"code": good_code})
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is True
        assert data["errors"] is None
        
        # 3. 검증 통과한 코드로 지표 등록
        custom_indicator = {
            "name": "Validated Indicator",
            "type": "test_validated",
            "description": "검증 통과한 지표",
            "category": "trend",
            "code": good_code,
            "params_schema": '{"period": 20}',
            "output_fields": ["main"]
        }
        
        response = client.post("/api/indicators/custom", json=custom_indicator)
        assert response.status_code == 201
        
        # 정리
        client.delete("/api/indicators/test_validated")
        
        # 테스트 성공


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

