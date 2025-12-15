"""
Indicators API 통합 테스트

FastAPI 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import json

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from apps.api.main import app

client = TestClient(app)


class TestIndicatorsAPI:
    """Indicators API 테스트"""
    
    def test_list_indicators(self):
        """지표 목록 조회 테스트"""
        response = client.get("/api/indicators/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "indicators" in data
        assert "total" in data
        assert isinstance(data["indicators"], list)
        assert data["total"] >= 4  # 최소 4개 내장 지표
        
        # 내장 지표 확인
        types = [ind["type"] for ind in data["indicators"]]
        assert "ema" in types
        assert "sma" in types
        assert "rsi" in types
        assert "atr" in types
    
    def test_list_indicators_with_filter(self):
        """카테고리 필터링 테스트"""
        response = client.get("/api/indicators/?category=trend")
        
        assert response.status_code == 200
        data = response.json()
        
        # 모든 지표가 trend 카테고리여야 함
        for ind in data["indicators"]:
            assert ind["category"] == "trend"
    
    def test_get_indicator(self):
        """지표 상세 조회 테스트"""
        response = client.get("/api/indicators/ema")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["type"] == "ema"
        assert data["name"] == "EMA"
        assert data["category"] == "trend"
        assert data["implementation_type"] == "builtin"
        assert "output_fields" in data
    
    def test_get_nonexistent_indicator(self):
        """존재하지 않는 지표 조회 테스트"""
        response = client.get("/api/indicators/nonexistent")
        
        assert response.status_code == 404
    
    def test_register_custom_indicator(self):
        """커스텀 지표 등록 테스트"""
        custom_indicator = {
            "name": "Test VWAP",
            "type": "test_vwap",
            "description": "테스트용 VWAP 지표",
            "category": "volume",
            "code": """def calculate_test_vwap(df, params):
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    return vwap.fillna(0)
""",
            "params_schema": "{}",
            "output_fields": ["main"]
        }
        
        response = client.post("/api/indicators/custom", json=custom_indicator)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["type"] == "test_vwap"
        assert data["implementation_type"] == "custom"
        
        # 정리 (삭제)
        client.delete(f"/api/indicators/{data['type']}")
    
    def test_register_duplicate_indicator(self):
        """중복 지표 등록 테스트"""
        custom_indicator = {
            "name": "Duplicate Test",
            "type": "test_duplicate",
            "description": "중복 테스트",
            "category": "trend",
            "code": """def calculate_test(df, params):
    return df['close']
""",
            "params_schema": "{}",
            "output_fields": ["main"]
        }
        
        # 첫 번째 등록
        response1 = client.post("/api/indicators/custom", json=custom_indicator)
        assert response1.status_code == 201
        
        # 두 번째 등록 (중복)
        response2 = client.post("/api/indicators/custom", json=custom_indicator)
        assert response2.status_code == 400
        assert "이미 등록된" in response2.json()["detail"]
        
        # 정리
        client.delete("/api/indicators/test_duplicate")
    
    def test_register_invalid_code(self):
        """잘못된 코드 등록 테스트"""
        custom_indicator = {
            "name": "Bad Code",
            "type": "test_bad_code",
            "description": "잘못된 코드",
            "category": "trend",
            "code": """def bad_code(df):
    import os
    return df['close']
""",
            "params_schema": "{}",
            "output_fields": ["main"]
        }
        
        response = client.post("/api/indicators/custom", json=custom_indicator)
        
        assert response.status_code == 400
        assert "코드 검증 실패" in response.json()["detail"]
    
    def test_update_custom_indicator(self):
        """커스텀 지표 수정 테스트"""
        # 먼저 등록
        custom_indicator = {
            "name": "Test Update",
            "type": "test_update",
            "description": "수정 테스트",
            "category": "trend",
            "code": """def calculate_test_update(df, params):
    return df['close']
""",
            "params_schema": "{}",
            "output_fields": ["main"]
        }
        
        response1 = client.post("/api/indicators/custom", json=custom_indicator)
        assert response1.status_code == 201
        
        # 수정
        update_data = {
            "description": "수정된 설명"
        }
        
        response2 = client.patch("/api/indicators/test_update", json=update_data)
        assert response2.status_code == 200
        
        data = response2.json()
        assert data["description"] == "수정된 설명"
        
        # 정리
        client.delete("/api/indicators/test_update")
    
    def test_update_builtin_indicator(self):
        """내장 지표 수정 시도 테스트 (실패해야 함)"""
        update_data = {
            "description": "수정 시도"
        }
        
        response = client.patch("/api/indicators/ema", json=update_data)
        
        assert response.status_code == 400
        assert "내장 지표" in response.json()["detail"]
    
    def test_delete_custom_indicator(self):
        """커스텀 지표 삭제 테스트"""
        # 먼저 등록
        custom_indicator = {
            "name": "Test Delete",
            "type": "test_delete",
            "description": "삭제 테스트",
            "category": "trend",
            "code": """def calculate_test_delete(df, params):
    return df['close']
""",
            "params_schema": "{}",
            "output_fields": ["main"]
        }
        
        response1 = client.post("/api/indicators/custom", json=custom_indicator)
        assert response1.status_code == 201
        
        # 삭제
        response2 = client.delete("/api/indicators/test_delete")
        assert response2.status_code == 204
        
        # 삭제 확인
        response3 = client.get("/api/indicators/test_delete")
        assert response3.status_code == 404
    
    def test_delete_builtin_indicator(self):
        """내장 지표 삭제 시도 테스트 (실패해야 함)"""
        response = client.delete("/api/indicators/ema")
        
        assert response.status_code == 400
        assert "내장 지표" in response.json()["detail"]
    
    def test_validate_code(self):
        """코드 검증 엔드포인트 테스트"""
        valid_code = """def test_indicator(df, params):
    return df['close']
"""
        
        response = client.post("/api/indicators/validate", json={"code": valid_code})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is True
        assert data["message"] == "코드 검증 통과"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

