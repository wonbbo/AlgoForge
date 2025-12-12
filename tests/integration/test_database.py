"""
데이터베이스 통합 테스트

이 모듈은 데이터베이스 연결, Repository, 유틸리티 함수들을 통합 테스트합니다.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import time

from apps.api.db.database import Database
from apps.api.db.repositories import (
    DatasetRepository,
    StrategyRepository,
    RunRepository,
    TradeRepository,
    TradeLegRepository,
    MetricsRepository
)
from apps.api.db.utils import (
    calculate_dataset_hash,
    calculate_strategy_hash,
    load_bars_from_csv,
    validate_bars,
    save_bars_to_csv,
    create_strategy_definition,
    load_strategy_from_json,
    save_strategy_to_json
)
from engine.models.bar import Bar
from engine.models.trade import Trade
from engine.models.trade_leg import TradeLeg
from engine.core.metrics_calculator import Metrics


class TestDatabase:
    """Database 클래스 테스트"""
    
    @pytest.fixture
    def temp_db(self):
        """임시 데이터베이스 생성"""
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test.db"
        
        # Database 인스턴스 생성
        db = Database(str(db_path))
        
        yield db
        
        # 정리
        shutil.rmtree(temp_dir)
    
    def test_database_creation(self, temp_db):
        """데이터베이스 파일 및 스키마 생성 테스트"""
        # 데이터베이스 파일이 생성되었는지 확인
        assert Path(temp_db.db_path).exists()
        
        # 테이블이 생성되었는지 확인
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'datasets', 'strategies', 'runs', 'trades', 'trade_legs', 'metrics'
        ]
        for table in expected_tables:
            assert table in tables
    
    def test_connection_context_manager(self, temp_db):
        """컨텍스트 매니저 테스트"""
        # 정상 케이스: 자동 커밋
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO datasets (name, dataset_hash, file_path, "
                "bars_count, start_timestamp, end_timestamp, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("test", "hash123", "/path/to/file", 100, 1000, 2000, int(time.time()))
            )
        
        # 데이터가 저장되었는지 확인
        results = temp_db.execute_query("SELECT * FROM datasets WHERE name = ?", ("test",))
        assert len(results) == 1
        assert results[0]['name'] == "test"
    
    def test_execute_query(self, temp_db):
        """execute_query 메서드 테스트"""
        # 데이터 삽입
        temp_db.execute_insert(
            "INSERT INTO datasets (name, dataset_hash, file_path, "
            "bars_count, start_timestamp, end_timestamp, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("test1", "hash1", "/path1", 100, 1000, 2000, int(time.time()))
        )
        temp_db.execute_insert(
            "INSERT INTO datasets (name, dataset_hash, file_path, "
            "bars_count, start_timestamp, end_timestamp, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("test2", "hash2", "/path2", 200, 3000, 4000, int(time.time()))
        )
        
        # 조회
        results = temp_db.execute_query("SELECT * FROM datasets ORDER BY name")
        assert len(results) == 2
        assert results[0]['name'] == "test1"
        assert results[1]['name'] == "test2"
    
    def test_execute_insert(self, temp_db):
        """execute_insert 메서드 테스트"""
        dataset_id = temp_db.execute_insert(
            "INSERT INTO datasets (name, dataset_hash, file_path, "
            "bars_count, start_timestamp, end_timestamp, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("test", "hash", "/path", 100, 1000, 2000, int(time.time()))
        )
        
        # ID가 반환되었는지 확인
        assert dataset_id > 0
        
        # 데이터가 저장되었는지 확인
        results = temp_db.execute_query(
            "SELECT * FROM datasets WHERE dataset_id = ?",
            (dataset_id,)
        )
        assert len(results) == 1
    
    def test_execute_update(self, temp_db):
        """execute_update 메서드 테스트"""
        # 데이터 삽입
        dataset_id = temp_db.execute_insert(
            "INSERT INTO datasets (name, dataset_hash, file_path, "
            "bars_count, start_timestamp, end_timestamp, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("test", "hash", "/path", 100, 1000, 2000, int(time.time()))
        )
        
        # 업데이트
        rowcount = temp_db.execute_update(
            "UPDATE datasets SET name = ? WHERE dataset_id = ?",
            ("updated", dataset_id)
        )
        
        assert rowcount == 1
        
        # 업데이트 확인
        results = temp_db.execute_query(
            "SELECT * FROM datasets WHERE dataset_id = ?",
            (dataset_id,)
        )
        assert results[0]['name'] == "updated"
    
    def test_execute_delete(self, temp_db):
        """execute_delete 메서드 테스트"""
        # 데이터 삽입
        dataset_id = temp_db.execute_insert(
            "INSERT INTO datasets (name, dataset_hash, file_path, "
            "bars_count, start_timestamp, end_timestamp, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("test", "hash", "/path", 100, 1000, 2000, int(time.time()))
        )
        
        # 삭제
        rowcount = temp_db.execute_delete(
            "DELETE FROM datasets WHERE dataset_id = ?",
            (dataset_id,)
        )
        
        assert rowcount == 1
        
        # 삭제 확인
        results = temp_db.execute_query(
            "SELECT * FROM datasets WHERE dataset_id = ?",
            (dataset_id,)
        )
        assert len(results) == 0


class TestRepositories:
    """Repository 클래스들 테스트"""
    
    @pytest.fixture
    def temp_db(self):
        """임시 데이터베이스 생성"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test.db"
        db = Database(str(db_path))
        yield db
        shutil.rmtree(temp_dir)
    
    def test_dataset_repository(self, temp_db):
        """DatasetRepository 테스트"""
        repo = DatasetRepository(temp_db)
        
        # 생성
        dataset_id = repo.create(
            name="Test Dataset",
            dataset_hash="hash123",
            file_path="/path/to/file.csv",
            bars_count=100,
            start_timestamp=1000,
            end_timestamp=2000,
            description="Test description"
        )
        
        assert dataset_id > 0
        
        # ID로 조회
        dataset = repo.get_by_id(dataset_id)
        assert dataset is not None
        assert dataset['name'] == "Test Dataset"
        assert dataset['dataset_hash'] == "hash123"
        
        # 해시로 조회
        dataset = repo.get_by_hash("hash123")
        assert dataset is not None
        assert dataset['dataset_id'] == dataset_id
        
        # 전체 조회
        datasets = repo.get_all()
        assert len(datasets) == 1
        
        # 삭제
        rowcount = repo.delete(dataset_id)
        assert rowcount == 1
        
        dataset = repo.get_by_id(dataset_id)
        assert dataset is None
    
    def test_strategy_repository(self, temp_db):
        """StrategyRepository 테스트"""
        repo = StrategyRepository(temp_db)
        
        # 생성
        definition = {
            'name': 'Test Strategy',
            'signals': [
                {'timestamp': 1000, 'direction': 'LONG', 'stop_loss': 100}
            ]
        }
        
        strategy_id = repo.create(
            name="Test Strategy",
            strategy_hash="strat_hash",
            definition=definition,
            description="Test strategy"
        )
        
        assert strategy_id > 0
        
        # ID로 조회
        strategy = repo.get_by_id(strategy_id)
        assert strategy is not None
        assert strategy['name'] == "Test Strategy"
        assert strategy['definition']['name'] == 'Test Strategy'
        
        # 해시로 조회
        strategy = repo.get_by_hash("strat_hash")
        assert strategy is not None
        assert strategy['strategy_id'] == strategy_id
        
        # 전체 조회
        strategies = repo.get_all()
        assert len(strategies) == 1
        
        # 삭제
        rowcount = repo.delete(strategy_id)
        assert rowcount == 1
    
    def test_run_repository(self, temp_db):
        """RunRepository 테스트"""
        # 먼저 dataset과 strategy 생성
        dataset_repo = DatasetRepository(temp_db)
        strategy_repo = StrategyRepository(temp_db)
        
        dataset_id = dataset_repo.create(
            name="Test Dataset",
            dataset_hash="hash",
            file_path="/path",
            bars_count=100,
            start_timestamp=1000,
            end_timestamp=2000
        )
        
        strategy_id = strategy_repo.create(
            name="Test Strategy",
            strategy_hash="strat_hash",
            definition={'signals': []}
        )
        
        # Run 생성
        run_repo = RunRepository(temp_db)
        run_id = run_repo.create(
            dataset_id=dataset_id,
            strategy_id=strategy_id,
            engine_version="1.0.0",
            initial_balance=10000.0,
            status="PENDING"
        )
        
        assert run_id > 0
        
        # 조회
        run = run_repo.get_by_id(run_id)
        assert run is not None
        assert run['status'] == "PENDING"
        assert run['engine_version'] == "1.0.0"
        
        # 상태 업데이트
        started_at = int(time.time())
        rowcount = run_repo.update_status(
            run_id=run_id,
            status="RUNNING",
            started_at=started_at
        )
        assert rowcount == 1
        
        run = run_repo.get_by_id(run_id)
        assert run['status'] == "RUNNING"
        assert run['started_at'] == started_at
        
        # dataset별 조회
        runs = run_repo.get_by_dataset(dataset_id)
        assert len(runs) == 1
        
        # strategy별 조회
        runs = run_repo.get_by_strategy(strategy_id)
        assert len(runs) == 1
    
    def test_trade_repository(self, temp_db):
        """TradeRepository 테스트"""
        # Run 생성
        dataset_repo = DatasetRepository(temp_db)
        strategy_repo = StrategyRepository(temp_db)
        run_repo = RunRepository(temp_db)
        
        dataset_id = dataset_repo.create(
            name="Test", dataset_hash="hash", file_path="/path",
            bars_count=100, start_timestamp=1000, end_timestamp=2000
        )
        strategy_id = strategy_repo.create(
            name="Test", strategy_hash="hash", definition={}
        )
        run_id = run_repo.create(
            dataset_id=dataset_id, strategy_id=strategy_id,
            engine_version="1.0.0", initial_balance=10000.0
        )
        
        # Trade 생성
        trade = Trade(
            trade_id=1,
            direction='LONG',
            entry_price=100.0,
            entry_timestamp=1000,
            position_size=1.0,
            initial_risk=5.0,
            stop_loss=95.0,
            take_profit_1=107.5,
            is_closed=True
        )
        
        # TradeLeg 추가
        leg = TradeLeg(
            trade_id=1,
            exit_type='TP1',
            exit_timestamp=1100,
            exit_price=107.5,
            qty_ratio=0.5,
            pnl=3.75
        )
        trade.add_leg(leg)
        
        # 데이터베이스에 저장
        trade_repo = TradeRepository(temp_db)
        db_trade_id = trade_repo.create_from_trade(run_id, trade)
        
        assert db_trade_id > 0
        
        # 조회
        db_trade = trade_repo.get_by_id(db_trade_id)
        assert db_trade is not None
        assert db_trade['direction'] == 'LONG'
        assert db_trade['entry_price'] == 100.0
        
        # Run별 조회
        trades = trade_repo.get_by_run(run_id)
        assert len(trades) == 1
    
    def test_trade_leg_repository(self, temp_db):
        """TradeLegRepository 테스트"""
        # Trade 생성 (위와 동일)
        dataset_repo = DatasetRepository(temp_db)
        strategy_repo = StrategyRepository(temp_db)
        run_repo = RunRepository(temp_db)
        trade_repo = TradeRepository(temp_db)
        
        dataset_id = dataset_repo.create(
            name="Test", dataset_hash="hash", file_path="/path",
            bars_count=100, start_timestamp=1000, end_timestamp=2000
        )
        strategy_id = strategy_repo.create(
            name="Test", strategy_hash="hash", definition={}
        )
        run_id = run_repo.create(
            dataset_id=dataset_id, strategy_id=strategy_id,
            engine_version="1.0.0", initial_balance=10000.0
        )
        
        trade = Trade(
            trade_id=1, direction='LONG', entry_price=100.0,
            entry_timestamp=1000, position_size=1.0, initial_risk=5.0,
            stop_loss=95.0, take_profit_1=107.5, is_closed=True
        )
        db_trade_id = trade_repo.create_from_trade(run_id, trade)
        
        # TradeLeg 생성
        leg_repo = TradeLegRepository(temp_db)
        
        leg1 = TradeLeg(
            trade_id=1, exit_type='TP1', exit_timestamp=1100,
            exit_price=107.5, qty_ratio=0.5, pnl=3.75
        )
        leg_id1 = leg_repo.create_from_trade_leg(db_trade_id, leg1)
        
        leg2 = TradeLeg(
            trade_id=1, exit_type='BE', exit_timestamp=1200,
            exit_price=100.0, qty_ratio=0.5, pnl=0.0
        )
        leg_id2 = leg_repo.create_from_trade_leg(db_trade_id, leg2)
        
        assert leg_id1 > 0
        assert leg_id2 > 0
        
        # Trade별 조회
        legs = leg_repo.get_by_trade(db_trade_id)
        assert len(legs) == 2
        assert legs[0]['exit_type'] == 'TP1'
        assert legs[1]['exit_type'] == 'BE'
    
    def test_metrics_repository(self, temp_db):
        """MetricsRepository 테스트"""
        # Run 생성
        dataset_repo = DatasetRepository(temp_db)
        strategy_repo = StrategyRepository(temp_db)
        run_repo = RunRepository(temp_db)
        
        dataset_id = dataset_repo.create(
            name="Test", dataset_hash="hash", file_path="/path",
            bars_count=100, start_timestamp=1000, end_timestamp=2000
        )
        strategy_id = strategy_repo.create(
            name="Test", strategy_hash="hash", definition={}
        )
        run_id = run_repo.create(
            dataset_id=dataset_id, strategy_id=strategy_id,
            engine_version="1.0.0", initial_balance=10000.0
        )
        
        # Metrics 생성
        metrics = Metrics(
            trades_count=10,
            winning_trades=7,
            losing_trades=3,
            win_rate=0.7,
            tp1_hit_rate=0.6,
            be_exit_rate=0.3,
            total_pnl=500.0,
            average_pnl=50.0,
            profit_factor=2.5,
            max_drawdown=-100.0,
            score=75.0,
            grade='A'
        )
        
        # 데이터베이스에 저장
        metrics_repo = MetricsRepository(temp_db)
        metric_id = metrics_repo.create_from_metrics(run_id, metrics)
        
        assert metric_id > 0
        
        # 조회
        db_metrics = metrics_repo.get_by_run(run_id)
        assert db_metrics is not None
        assert db_metrics['trades_count'] == 10
        assert db_metrics['win_rate'] == 0.7
        assert db_metrics['grade'] == 'A'


class TestUtils:
    """유틸리티 함수 테스트"""
    
    def test_calculate_dataset_hash(self):
        """dataset_hash 계산 테스트"""
        bars1 = [
            Bar(1000, 100.0, 105.0, 99.0, 103.0, 1000.0, 1),
            Bar(1100, 103.0, 108.0, 102.0, 107.0, 1200.0, 1),
        ]
        
        bars2 = [
            Bar(1000, 100.0, 105.0, 99.0, 103.0, 1000.0, 1),
            Bar(1100, 103.0, 108.0, 102.0, 107.0, 1200.0, 1),
        ]
        
        # 동일한 데이터 → 동일한 해시
        hash1 = calculate_dataset_hash(bars1)
        hash2 = calculate_dataset_hash(bars2)
        assert hash1 == hash2
        
        # 다른 데이터 → 다른 해시
        bars3 = [
            Bar(1000, 100.0, 105.0, 99.0, 103.0, 1000.0, 1),
            Bar(1100, 103.0, 108.0, 102.0, 108.0, 1200.0, 1),  # close 다름
        ]
        hash3 = calculate_dataset_hash(bars3)
        assert hash1 != hash3
    
    def test_calculate_strategy_hash(self):
        """strategy_hash 계산 테스트"""
        def1 = {
            'name': 'Test',
            'signals': [{'timestamp': 1000, 'direction': 'LONG'}]
        }
        
        def2 = {
            'signals': [{'timestamp': 1000, 'direction': 'LONG'}],
            'name': 'Test'  # 순서 다름
        }
        
        # 동일한 내용 → 동일한 해시 (키 정렬됨)
        hash1 = calculate_strategy_hash(def1)
        hash2 = calculate_strategy_hash(def2)
        assert hash1 == hash2
        
        # 다른 내용 → 다른 해시
        def3 = {
            'name': 'Test',
            'signals': [{'timestamp': 1000, 'direction': 'SHORT'}]  # direction 다름
        }
        hash3 = calculate_strategy_hash(def3)
        assert hash1 != hash3
    
    def test_validate_bars(self):
        """봉 데이터 검증 테스트"""
        # 정상 케이스
        bars = [
            Bar(1000, 100.0, 105.0, 99.0, 103.0, 1000.0, 1),
            Bar(1100, 103.0, 108.0, 102.0, 107.0, 1200.0, 1),
        ]
        is_valid, errors = validate_bars(bars)
        assert is_valid
        assert len(errors) == 0
        
        # timestamp 미정렬
        bars_unsorted = [
            Bar(1100, 103.0, 108.0, 102.0, 107.0, 1200.0, 1),
            Bar(1000, 100.0, 105.0, 99.0, 103.0, 1000.0, 1),
        ]
        is_valid, errors = validate_bars(bars_unsorted)
        assert not is_valid
        assert len(errors) > 0
        
        # 빈 리스트
        is_valid, errors = validate_bars([])
        assert not is_valid
        assert len(errors) > 0
    
    def test_save_and_load_bars_csv(self):
        """CSV 저장 및 로드 테스트"""
        bars = [
            Bar(1000, 100.0, 105.0, 99.0, 103.0, 1000.0, 1),
            Bar(1100, 103.0, 108.0, 102.0, 107.0, 1200.0, 1),
        ]
        
        # 임시 파일에 저장
        temp_dir = tempfile.mkdtemp()
        csv_path = Path(temp_dir) / "test.csv"
        
        save_bars_to_csv(bars, str(csv_path))
        
        # 로드
        loaded_bars, metadata = load_bars_from_csv(str(csv_path))
        
        # 검증
        assert len(loaded_bars) == 2
        assert loaded_bars[0].timestamp == 1000
        assert loaded_bars[1].timestamp == 1100
        assert metadata['bars_count'] == 2
        assert metadata['start_timestamp'] == 1000
        assert metadata['end_timestamp'] == 1100
        
        # 정리
        shutil.rmtree(temp_dir)
    
    def test_create_strategy_definition(self):
        """전략 정의 생성 테스트"""
        signals = [
            {'timestamp': 1000, 'direction': 'LONG', 'stop_loss': 95.0}
        ]
        
        definition = create_strategy_definition(
            name="Test Strategy",
            signals=signals,
            description="Test description"
        )
        
        assert definition['name'] == "Test Strategy"
        assert definition['description'] == "Test description"
        assert len(definition['signals']) == 1
    
    def test_save_and_load_strategy_json(self):
        """JSON 저장 및 로드 테스트"""
        definition = {
            'name': 'Test Strategy',
            'signals': [
                {'timestamp': 1000, 'direction': 'LONG', 'stop_loss': 95.0}
            ]
        }
        
        # 임시 파일에 저장
        temp_dir = tempfile.mkdtemp()
        json_path = Path(temp_dir) / "test.json"
        
        save_strategy_to_json(definition, str(json_path))
        
        # 로드
        loaded_definition = load_strategy_from_json(str(json_path))
        
        # 검증
        assert loaded_definition['name'] == 'Test Strategy'
        assert len(loaded_definition['signals']) == 1
        
        # 정리
        shutil.rmtree(temp_dir)

