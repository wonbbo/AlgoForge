"""
API 통합 테스트

FastAPI 엔드포인트를 테스트합니다.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json
import time
import tempfile
import shutil

from apps.api.main import app
from apps.api.db.database import Database


class TestAPI:
    """API 통합 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient fixture"""
        # 테스트용 임시 데이터베이스 사용
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db_path = Path(tmpdir) / "test.db"
            
            # 테스트용 데이터베이스 초기화
            test_db = Database(str(test_db_path))
            
            # TestClient 생성
            client = TestClient(app)
            
            yield client
            
            # 정리
            del test_db
    
    @pytest.fixture
    def test_data_dir(self):
        """테스트 데이터 디렉토리"""
        return Path(__file__).parent.parent / "fixtures"
    
    def test_root_endpoint(self, client):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AlgoForge API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        """헬스 체크 테스트"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_dataset_upload(self, client, test_data_dir):
        """데이터셋 업로드 테스트"""
        # CSV 파일 준비
        csv_file = test_data_dir / "test_data_A.csv"
        
        with open(csv_file, "rb") as f:
            response = client.post(
                "/api/datasets",
                files={"file": ("test_data_A.csv", f, "text/csv")},
                data={
                    "name": "Test Dataset A",
                    "description": "Test dataset for API testing",
                    "timeframe": "5m"
                }
            )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "dataset_id" in data
        assert data["name"] == "Test Dataset A"
        assert data["timeframe"] == "5m"
        assert "dataset_hash" in data
    
    def test_dataset_list(self, client, test_data_dir):
        """데이터셋 목록 조회 테스트"""
        # 먼저 데이터셋 업로드
        csv_file = test_data_dir / "test_data_A.csv"
        
        with open(csv_file, "rb") as f:
            client.post(
                "/api/datasets",
                files={"file": ("test_data_A.csv", f, "text/csv")},
                data={"name": "Test Dataset A"}
            )
        
        # 목록 조회
        response = client.get("/api/datasets")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "datasets" in data
        assert "total" in data
        assert data["total"] > 0
    
    def test_dataset_get(self, client, test_data_dir):
        """데이터셋 상세 조회 테스트"""
        # 먼저 데이터셋 업로드
        csv_file = test_data_dir / "test_data_A.csv"
        
        with open(csv_file, "rb") as f:
            create_response = client.post(
                "/api/datasets",
                files={"file": ("test_data_A.csv", f, "text/csv")},
                data={"name": "Test Dataset A"}
            )
        
        dataset_id = create_response.json()["dataset_id"]
        
        # 상세 조회
        response = client.get(f"/api/datasets/{dataset_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["dataset_id"] == dataset_id
        assert data["name"] == "Test Dataset A"
    
    def test_dataset_delete(self, client, test_data_dir):
        """데이터셋 삭제 테스트"""
        # 먼저 데이터셋 업로드
        csv_file = test_data_dir / "test_data_A.csv"
        
        with open(csv_file, "rb") as f:
            create_response = client.post(
                "/api/datasets",
                files={"file": ("test_data_A.csv", f, "text/csv")},
                data={"name": "Test Dataset A"}
            )
        
        dataset_id = create_response.json()["dataset_id"]
        
        # 삭제
        response = client.delete(f"/api/datasets/{dataset_id}")
        
        assert response.status_code == 204
        
        # 삭제 확인
        get_response = client.get(f"/api/datasets/{dataset_id}")
        assert get_response.status_code == 404
    
    def test_strategy_create(self, client):
        """전략 생성 테스트"""
        strategy_data = {
            "name": "Test Strategy",
            "description": "Test strategy for API testing",
            "definition": {
                "entry_long": {"indicator": "ema_cross", "params": {"fast": 12, "slow": 26}},
                "entry_short": {"indicator": "ema_cross_down", "params": {"fast": 12, "slow": 26}}
            }
        }
        
        response = client.post("/api/strategies", json=strategy_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert "strategy_id" in data
        assert data["name"] == "Test Strategy"
        assert "strategy_hash" in data
        assert data["definition"] == strategy_data["definition"]
    
    def test_strategy_list(self, client):
        """전략 목록 조회 테스트"""
        # 먼저 전략 생성
        strategy_data = {
            "name": "Test Strategy",
            "definition": {"entry_long": {}, "entry_short": {}}
        }
        
        client.post("/api/strategies", json=strategy_data)
        
        # 목록 조회
        response = client.get("/api/strategies")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "strategies" in data
        assert "total" in data
        assert data["total"] > 0
    
    def test_strategy_get(self, client):
        """전략 상세 조회 테스트"""
        # 먼저 전략 생성
        strategy_data = {
            "name": "Test Strategy",
            "definition": {"entry_long": {}, "entry_short": {}}
        }
        
        create_response = client.post("/api/strategies", json=strategy_data)
        strategy_id = create_response.json()["strategy_id"]
        
        # 상세 조회
        response = client.get(f"/api/strategies/{strategy_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["strategy_id"] == strategy_id
        assert data["name"] == "Test Strategy"
    
    def test_strategy_delete(self, client):
        """전략 삭제 테스트"""
        # 먼저 전략 생성
        strategy_data = {
            "name": "Test Strategy",
            "definition": {"entry_long": {}, "entry_short": {}}
        }
        
        create_response = client.post("/api/strategies", json=strategy_data)
        strategy_id = create_response.json()["strategy_id"]
        
        # 삭제
        response = client.delete(f"/api/strategies/{strategy_id}")
        
        assert response.status_code == 204
        
        # 삭제 확인
        get_response = client.get(f"/api/strategies/{strategy_id}")
        assert get_response.status_code == 404
    
    def test_run_create(self, client, test_data_dir):
        """Run 생성 테스트"""
        # Dataset 생성
        csv_file = test_data_dir / "test_data_A.csv"
        
        with open(csv_file, "rb") as f:
            dataset_response = client.post(
                "/api/datasets",
                files={"file": ("test_data_A.csv", f, "text/csv")},
                data={"name": "Test Dataset A"}
            )
        
        dataset_id = dataset_response.json()["dataset_id"]
        
        # Strategy 생성
        strategy_data = {
            "name": "Test Strategy",
            "definition": {"entry_long": {}, "entry_short": {}}
        }
        
        strategy_response = client.post("/api/strategies", json=strategy_data)
        strategy_id = strategy_response.json()["strategy_id"]
        
        # Run 생성
        run_data = {
            "dataset_id": dataset_id,
            "strategy_id": strategy_id,
            "initial_balance": 10000.0
        }
        
        response = client.post("/api/runs", json=run_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert "run_id" in data
        assert data["dataset_id"] == dataset_id
        assert data["strategy_id"] == strategy_id
        assert data["status"] == "PENDING"
    
    def test_run_list(self, client, test_data_dir):
        """Run 목록 조회 테스트"""
        # Dataset, Strategy, Run 생성
        csv_file = test_data_dir / "test_data_A.csv"
        
        with open(csv_file, "rb") as f:
            dataset_response = client.post(
                "/api/datasets",
                files={"file": ("test_data_A.csv", f, "text/csv")},
                data={"name": "Test Dataset A"}
            )
        
        dataset_id = dataset_response.json()["dataset_id"]
        
        strategy_response = client.post(
            "/api/strategies",
            json={"name": "Test Strategy", "definition": {}}
        )
        strategy_id = strategy_response.json()["strategy_id"]
        
        client.post(
            "/api/runs",
            json={"dataset_id": dataset_id, "strategy_id": strategy_id}
        )
        
        # 목록 조회
        response = client.get("/api/runs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "runs" in data
        assert "total" in data
        assert data["total"] > 0
    
    def test_run_get(self, client, test_data_dir):
        """Run 상세 조회 테스트"""
        # Dataset, Strategy, Run 생성
        csv_file = test_data_dir / "test_data_A.csv"
        
        with open(csv_file, "rb") as f:
            dataset_response = client.post(
                "/api/datasets",
                files={"file": ("test_data_A.csv", f, "text/csv")},
                data={"name": "Test Dataset A"}
            )
        
        dataset_id = dataset_response.json()["dataset_id"]
        
        strategy_response = client.post(
            "/api/strategies",
            json={"name": "Test Strategy", "definition": {}}
        )
        strategy_id = strategy_response.json()["strategy_id"]
        
        run_response = client.post(
            "/api/runs",
            json={"dataset_id": dataset_id, "strategy_id": strategy_id}
        )
        run_id = run_response.json()["run_id"]
        
        # 상세 조회
        response = client.get(f"/api/runs/{run_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["run_id"] == run_id
        assert data["dataset_id"] == dataset_id
        assert data["strategy_id"] == strategy_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

