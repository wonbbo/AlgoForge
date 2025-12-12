"""
데이터베이스 Repository 클래스들

이 모듈은 각 테이블에 대한 CRUD 로직을 제공합니다.
- DatasetRepository: datasets 테이블 관리
- StrategyRepository: strategies 테이블 관리
- RunRepository: runs 테이블 관리
- TradeRepository: trades 테이블 관리
- TradeLegRepository: trade_legs 테이블 관리
- MetricsRepository: metrics 테이블 관리
"""

import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import asdict

from apps.api.db.database import Database
from engine.models.trade import Trade
from engine.models.trade_leg import TradeLeg
from engine.core.metrics_calculator import Metrics


class DatasetRepository:
    """
    datasets 테이블 관리 Repository
    
    주요 기능:
    - 데이터셋 생성, 조회, 삭제
    - dataset_hash 기반 중복 체크
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(
        self,
        name: str,
        dataset_hash: str,
        file_path: str,
        bars_count: int,
        start_timestamp: int,
        end_timestamp: int,
        description: Optional[str] = None,
        timeframe: str = "5m"
    ) -> int:
        """
        데이터셋 생성
        
        Args:
            name: 데이터셋 이름
            dataset_hash: 데이터셋 해시 (중복 체크용)
            file_path: CSV 파일 경로
            bars_count: 봉 개수
            start_timestamp: 시작 timestamp
            end_timestamp: 종료 timestamp
            description: 설명 (선택)
            timeframe: 타임프레임 (기본값: 5m)
            
        Returns:
            int: 생성된 dataset_id
        """
        query = """
        INSERT INTO datasets (
            name, description, timeframe, dataset_hash, file_path,
            bars_count, start_timestamp, end_timestamp, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        created_at = int(time.time())
        
        return self.db.execute_insert(
            query,
            (name, description, timeframe, dataset_hash, file_path,
             bars_count, start_timestamp, end_timestamp, created_at)
        )
    
    def get_by_id(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """
        dataset_id로 데이터셋 조회
        
        Args:
            dataset_id: 데이터셋 ID
            
        Returns:
            Optional[Dict[str, Any]]: 데이터셋 정보 (없으면 None)
        """
        query = "SELECT * FROM datasets WHERE dataset_id = ?"
        results = self.db.execute_query(query, (dataset_id,))
        
        if results:
            return dict(results[0])
        return None
    
    def get_by_hash(self, dataset_hash: str) -> Optional[Dict[str, Any]]:
        """
        dataset_hash로 데이터셋 조회
        
        Args:
            dataset_hash: 데이터셋 해시
            
        Returns:
            Optional[Dict[str, Any]]: 데이터셋 정보 (없으면 None)
        """
        query = "SELECT * FROM datasets WHERE dataset_hash = ?"
        results = self.db.execute_query(query, (dataset_hash,))
        
        if results:
            return dict(results[0])
        return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        모든 데이터셋 조회
        
        Returns:
            List[Dict[str, Any]]: 데이터셋 목록
        """
        query = "SELECT * FROM datasets ORDER BY created_at DESC"
        results = self.db.execute_query(query)
        return [dict(row) for row in results]
    
    def delete(self, dataset_id: int) -> int:
        """
        데이터셋 삭제
        
        Args:
            dataset_id: 데이터셋 ID
            
        Returns:
            int: 삭제된 행 수
        """
        query = "DELETE FROM datasets WHERE dataset_id = ?"
        return self.db.execute_delete(query, (dataset_id,))


class StrategyRepository:
    """
    strategies 테이블 관리 Repository
    
    주요 기능:
    - 전략 생성, 조회, 삭제
    - strategy_hash 기반 조회
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(
        self,
        name: str,
        strategy_hash: str,
        definition: Dict[str, Any],
        description: Optional[str] = None
    ) -> int:
        """
        전략 생성
        
        Args:
            name: 전략 이름
            strategy_hash: 전략 해시
            definition: 전략 정의 (JSON으로 저장)
            description: 설명 (선택)
            
        Returns:
            int: 생성된 strategy_id
        """
        query = """
        INSERT INTO strategies (
            name, description, strategy_hash, definition, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """
        
        created_at = int(time.time())
        definition_json = json.dumps(definition, ensure_ascii=False)
        
        return self.db.execute_insert(
            query,
            (name, description, strategy_hash, definition_json, created_at)
        )
    
    def get_by_id(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """
        strategy_id로 전략 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            Optional[Dict[str, Any]]: 전략 정보 (없으면 None)
        """
        query = "SELECT * FROM strategies WHERE strategy_id = ?"
        results = self.db.execute_query(query, (strategy_id,))
        
        if results:
            row = dict(results[0])
            # JSON 문자열을 딕셔너리로 변환
            row['definition'] = json.loads(row['definition'])
            return row
        return None
    
    def get_by_hash(self, strategy_hash: str) -> Optional[Dict[str, Any]]:
        """
        strategy_hash로 전략 조회
        
        Args:
            strategy_hash: 전략 해시
            
        Returns:
            Optional[Dict[str, Any]]: 전략 정보 (없으면 None)
        """
        query = "SELECT * FROM strategies WHERE strategy_hash = ?"
        results = self.db.execute_query(query, (strategy_hash,))
        
        if results:
            row = dict(results[0])
            row['definition'] = json.loads(row['definition'])
            return row
        return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        모든 전략 조회
        
        Returns:
            List[Dict[str, Any]]: 전략 목록
        """
        query = "SELECT * FROM strategies ORDER BY created_at DESC"
        results = self.db.execute_query(query)
        
        strategies = []
        for row in results:
            strategy = dict(row)
            strategy['definition'] = json.loads(strategy['definition'])
            strategies.append(strategy)
        
        return strategies
    
    def delete(self, strategy_id: int) -> int:
        """
        전략 삭제
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            int: 삭제된 행 수
        """
        query = "DELETE FROM strategies WHERE strategy_id = ?"
        return self.db.execute_delete(query, (strategy_id,))


class RunRepository:
    """
    runs 테이블 관리 Repository
    
    주요 기능:
    - Run 생성, 조회, 상태 업데이트
    - 결정성 보장을 위한 중복 Run 체크
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(
        self,
        dataset_id: int,
        strategy_id: int,
        engine_version: str,
        initial_balance: float,
        status: str = "PENDING"
    ) -> int:
        """
        Run 생성
        
        Args:
            dataset_id: 데이터셋 ID
            strategy_id: 전략 ID
            engine_version: 엔진 버전
            initial_balance: 초기 자산
            status: 상태 (기본값: PENDING)
            
        Returns:
            int: 생성된 run_id
        """
        query = """
        INSERT INTO runs (
            dataset_id, strategy_id, status, engine_version, initial_balance
        ) VALUES (?, ?, ?, ?, ?)
        """
        
        return self.db.execute_insert(
            query,
            (dataset_id, strategy_id, status, engine_version, initial_balance)
        )
    
    def get_by_id(self, run_id: int) -> Optional[Dict[str, Any]]:
        """
        run_id로 Run 조회
        
        Args:
            run_id: Run ID
            
        Returns:
            Optional[Dict[str, Any]]: Run 정보 (없으면 None)
        """
        query = "SELECT * FROM runs WHERE run_id = ?"
        results = self.db.execute_query(query, (run_id,))
        
        if results:
            row = dict(results[0])
            # run_artifacts가 있으면 JSON 파싱
            if row['run_artifacts']:
                row['run_artifacts'] = json.loads(row['run_artifacts'])
            return row
        return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        모든 Run 조회
        
        Returns:
            List[Dict[str, Any]]: Run 목록
        """
        query = "SELECT * FROM runs ORDER BY run_id DESC"
        results = self.db.execute_query(query)
        
        runs = []
        for row in results:
            run = dict(row)
            if run['run_artifacts']:
                run['run_artifacts'] = json.loads(run['run_artifacts'])
            runs.append(run)
        
        return runs
    
    def get_by_dataset(self, dataset_id: int) -> List[Dict[str, Any]]:
        """
        특정 데이터셋의 모든 Run 조회
        
        Args:
            dataset_id: 데이터셋 ID
            
        Returns:
            List[Dict[str, Any]]: Run 목록
        """
        query = "SELECT * FROM runs WHERE dataset_id = ? ORDER BY run_id DESC"
        results = self.db.execute_query(query, (dataset_id,))
        
        runs = []
        for row in results:
            run = dict(row)
            if run['run_artifacts']:
                run['run_artifacts'] = json.loads(run['run_artifacts'])
            runs.append(run)
        
        return runs
    
    def get_by_strategy(self, strategy_id: int) -> List[Dict[str, Any]]:
        """
        특정 전략의 모든 Run 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            List[Dict[str, Any]]: Run 목록
        """
        query = "SELECT * FROM runs WHERE strategy_id = ? ORDER BY run_id DESC"
        results = self.db.execute_query(query, (strategy_id,))
        
        runs = []
        for row in results:
            run = dict(row)
            if run['run_artifacts']:
                run['run_artifacts'] = json.loads(run['run_artifacts'])
            runs.append(run)
        
        return runs
    
    def update_status(
        self,
        run_id: int,
        status: str,
        started_at: Optional[int] = None,
        completed_at: Optional[int] = None,
        run_artifacts: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Run 상태 업데이트
        
        Args:
            run_id: Run ID
            status: 상태 (PENDING, RUNNING, COMPLETED, FAILED)
            started_at: 시작 시각 (선택)
            completed_at: 완료 시각 (선택)
            run_artifacts: 실행 결과 메타데이터 (선택)
            
        Returns:
            int: 영향받은 행 수
        """
        # 동적 쿼리 생성
        fields = ["status = ?"]
        params = [status]
        
        if started_at is not None:
            fields.append("started_at = ?")
            params.append(started_at)
        
        if completed_at is not None:
            fields.append("completed_at = ?")
            params.append(completed_at)
        
        if run_artifacts is not None:
            fields.append("run_artifacts = ?")
            params.append(json.dumps(run_artifacts, ensure_ascii=False))
        
        params.append(run_id)
        
        query = f"UPDATE runs SET {', '.join(fields)} WHERE run_id = ?"
        return self.db.execute_update(query, tuple(params))
    
    def delete(self, run_id: int) -> int:
        """
        Run 삭제 (관련된 모든 데이터를 함께 삭제)
        
        Args:
            run_id: Run ID
            
        Returns:
            int: 삭제된 run 행 수
            
        Note:
            Foreign Key 제약 조건 때문에 다음 순서로 삭제합니다:
            1. trade_legs (trade_id를 통해)
            2. trades (run_id를 통해)
            3. metrics (run_id를 통해)
            4. runs
        """
        # 1. 이 Run의 모든 trade_id 조회
        trades_query = "SELECT trade_id FROM trades WHERE run_id = ?"
        trades = self.db.execute_query(trades_query, (run_id,))
        
        # 2. 각 trade의 trade_legs 삭제
        for trade in trades:
            trade_id = trade["trade_id"]
            legs_query = "DELETE FROM trade_legs WHERE trade_id = ?"
            self.db.execute_delete(legs_query, (trade_id,))
        
        # 3. trades 삭제
        trades_delete_query = "DELETE FROM trades WHERE run_id = ?"
        self.db.execute_delete(trades_delete_query, (run_id,))
        
        # 4. metrics 삭제
        metrics_query = "DELETE FROM metrics WHERE run_id = ?"
        self.db.execute_delete(metrics_query, (run_id,))
        
        # 5. run 삭제
        run_query = "DELETE FROM runs WHERE run_id = ?"
        return self.db.execute_delete(run_query, (run_id,))


class TradeRepository:
    """
    trades 테이블 관리 Repository
    
    주요 기능:
    - Trade 생성, 조회
    - Run별 Trade 조회
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_from_trade(self, run_id: int, trade: Trade) -> int:
        """
        Trade 객체로부터 데이터베이스 레코드 생성
        
        Args:
            run_id: Run ID
            trade: Trade 객체
            
        Returns:
            int: 생성된 trade_id
        """
        query = """
        INSERT INTO trades (
            run_id, direction, entry_timestamp, entry_price,
            position_size, initial_risk, stop_loss, take_profit_1,
            is_closed, total_pnl
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        return self.db.execute_insert(
            query,
            (
                run_id,
                trade.direction,
                trade.entry_timestamp,
                trade.entry_price,
                trade.position_size,
                trade.initial_risk,
                trade.stop_loss,
                trade.take_profit_1,
                1 if trade.is_closed else 0,
                trade.calculate_total_pnl()
            )
        )
    
    def get_by_run(self, run_id: int) -> List[Dict[str, Any]]:
        """
        특정 Run의 모든 Trade 조회
        
        Args:
            run_id: Run ID
            
        Returns:
            List[Dict[str, Any]]: Trade 목록
        """
        query = "SELECT * FROM trades WHERE run_id = ? ORDER BY entry_timestamp"
        results = self.db.execute_query(query, (run_id,))
        return [dict(row) for row in results]
    
    def get_by_id(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """
        trade_id로 Trade 조회
        
        Args:
            trade_id: Trade ID
            
        Returns:
            Optional[Dict[str, Any]]: Trade 정보 (없으면 None)
        """
        query = "SELECT * FROM trades WHERE trade_id = ?"
        results = self.db.execute_query(query, (trade_id,))
        
        if results:
            return dict(results[0])
        return None


class TradeLegRepository:
    """
    trade_legs 테이블 관리 Repository
    
    주요 기능:
    - TradeLeg 생성, 조회
    - Trade별 TradeLeg 조회
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_from_trade_leg(self, trade_id: int, leg: TradeLeg) -> int:
        """
        TradeLeg 객체로부터 데이터베이스 레코드 생성
        
        Args:
            trade_id: Trade ID (데이터베이스의 trade_id)
            leg: TradeLeg 객체
            
        Returns:
            int: 생성된 leg_id
        """
        query = """
        INSERT INTO trade_legs (
            trade_id, exit_type, exit_timestamp, exit_price,
            qty_ratio, pnl
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        return self.db.execute_insert(
            query,
            (
                trade_id,
                leg.exit_type,
                leg.exit_timestamp,
                leg.exit_price,
                leg.qty_ratio,
                leg.pnl
            )
        )
    
    def get_by_trade(self, trade_id: int) -> List[Dict[str, Any]]:
        """
        특정 Trade의 모든 TradeLeg 조회
        
        Args:
            trade_id: Trade ID
            
        Returns:
            List[Dict[str, Any]]: TradeLeg 목록
        """
        query = "SELECT * FROM trade_legs WHERE trade_id = ? ORDER BY exit_timestamp"
        results = self.db.execute_query(query, (trade_id,))
        return [dict(row) for row in results]


class MetricsRepository:
    """
    metrics 테이블 관리 Repository
    
    주요 기능:
    - Metrics 생성, 조회
    - Run별 Metrics 조회
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_from_metrics(self, run_id: int, metrics: Metrics) -> int:
        """
        Metrics 객체로부터 데이터베이스 레코드 생성
        
        Args:
            run_id: Run ID
            metrics: Metrics 객체
            
        Returns:
            int: 생성된 metric_id
        """
        query = """
        INSERT INTO metrics (
            run_id, trades_count, winning_trades, losing_trades,
            win_rate, tp1_hit_rate, be_exit_rate, total_pnl,
            average_pnl, profit_factor, max_drawdown, score, grade
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        return self.db.execute_insert(
            query,
            (
                run_id,
                metrics.trades_count,
                metrics.winning_trades,
                metrics.losing_trades,
                metrics.win_rate,
                metrics.tp1_hit_rate,
                metrics.be_exit_rate,
                metrics.total_pnl,
                metrics.average_pnl,
                metrics.profit_factor,
                metrics.max_drawdown,
                metrics.score,
                metrics.grade
            )
        )
    
    def get_by_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        """
        특정 Run의 Metrics 조회
        
        Args:
            run_id: Run ID
            
        Returns:
            Optional[Dict[str, Any]]: Metrics 정보 (없으면 None)
        """
        query = "SELECT * FROM metrics WHERE run_id = ?"
        results = self.db.execute_query(query, (run_id,))
        
        if results:
            return dict(results[0])
        return None

