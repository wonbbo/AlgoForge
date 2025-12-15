"""
SQLite 데이터베이스 연결 및 관리 모듈

이 모듈은 AlgoForge의 SQLite 데이터베이스 연결을 관리합니다.
- WAL 모드 활성화
- 컨텍스트 매니저 기반 연결 관리
- 자동 스키마 초기화
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite 데이터베이스 관리 클래스
    
    주요 기능:
    - 데이터베이스 파일 및 스키마 자동 생성
    - WAL 모드 활성화
    - 트랜잭션 관리
    - 컨텍스트 매니저 기반 연결
    """
    
    def __init__(self, db_path: str = "db/algoforge.db"):
        """
        Database 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로 (기본값: db/algoforge.db)
        """
        self.db_path = db_path
        self._ensure_db_exists()
        logger.info(f"Database initialized: {self.db_path}")
    
    def _ensure_db_exists(self) -> None:
        """
        데이터베이스 파일 및 스키마 생성
        
        - db 디렉토리가 없으면 생성
        - 스키마 파일이 있으면 자동 적용
        - WAL 모드 활성화
        """
        # db 디렉토리 생성
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 스키마 파일 경로 찾기
        # apps/api/db/database.py -> algoforge/db/schema.sql
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        schema_path = project_root / 'db' / 'schema.sql'
        
        logger.info(f"Looking for schema at: {schema_path.absolute()}")
        
        if not schema_path.exists():
            logger.warning(f"Schema file not found: {schema_path}")
            return
        
        # 핵심 테이블 존재 여부 확인 (datasets, indicators)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='datasets'"
                )
                datasets_exists = cursor.fetchone() is not None
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='indicators'"
                )
                indicators_exists = cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f"Failed to check table existence: {e}")
            datasets_exists = False
            indicators_exists = False
        
        # 테이블이 없으면 스키마 전체 적용 (idempotent)
        if not datasets_exists or not indicators_exists:
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = f.read()
                
                with self.get_connection() as conn:
                    conn.executescript(schema)
                
                logger.info("Database schema applied successfully")
            except Exception as e:
                logger.error(f"Failed to apply schema: {e}")
                raise
        else:
            logger.info("Database schema already exists, skipping initialization")
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        데이터베이스 연결 컨텍스트 매니저
        
        사용 예시:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM datasets")
                
        특징:
        - 자동 커밋 (성공 시)
        - 자동 롤백 (에러 시)
        - 자동 연결 종료
        - Row factory 설정 (딕셔너리 형태로 결과 반환)
        - WAL 모드 활성화
        
        Yields:
            sqlite3.Connection: 데이터베이스 연결 객체
        """
        conn = sqlite3.connect(self.db_path)
        # Row factory 설정: 결과를 딕셔너리 형태로 반환
        conn.row_factory = sqlite3.Row
        
        # WAL 모드 활성화 (성능 향상 및 동시 접근 지원)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        # 동기화 모드를 NORMAL로 설정 (WAL 모드에서 안전하면서도 빠름)
        # FULL: 모든 커밋마다 fsync() → 안전하지만 매우 느림
        # NORMAL: 중요한 순간에만 fsync() → WAL 모드에서 충분히 안전하고 빠름
        conn.execute("PRAGMA synchronous=NORMAL")
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            conn.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> list[sqlite3.Row]:
        """
        SELECT 쿼리 실행 및 결과 반환
        
        Args:
            query: SQL 쿼리 문자열
            params: 쿼리 파라미터 (선택)
            
        Returns:
            list[sqlite3.Row]: 쿼리 결과 리스트
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_insert(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> int:
        """
        INSERT 쿼리 실행 및 생성된 ID 반환
        
        Args:
            query: SQL INSERT 쿼리 문자열
            params: 쿼리 파라미터 (선택)
            
        Returns:
            int: 생성된 레코드의 ID (AUTOINCREMENT)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid
    
    def execute_update(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> int:
        """
        UPDATE 쿼리 실행 및 영향받은 행 수 반환
        
        Args:
            query: SQL UPDATE 쿼리 문자열
            params: 쿼리 파라미터 (선택)
            
        Returns:
            int: 영향받은 행 수
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def execute_delete(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> int:
        """
        DELETE 쿼리 실행 및 삭제된 행 수 반환
        
        Args:
            query: SQL DELETE 쿼리 문자열
            params: 쿼리 파라미터 (선택)
            
        Returns:
            int: 삭제된 행 수
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def execute_bulk_insert(
        self,
        query: str,
        data: list
    ) -> int:
        """
        대량 INSERT 쿼리 실행 (executemany 사용)
        
        Args:
            query: SQL INSERT 쿼리 문자열
            data: 파라미터 리스트 (각 항목은 tuple)
            
        Returns:
            int: 삽입된 행 수
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, data)
            return cursor.rowcount
    
    def reset_database(self) -> None:
        """
        데이터베이스 초기화 (모든 테이블 삭제 후 재생성)
        
        주의: 모든 데이터가 삭제됩니다!
        테스트 용도로만 사용하세요.
        """
        logger.warning("Resetting database - all data will be lost!")
        
        # 데이터베이스 파일 삭제
        db_path = Path(self.db_path)
        if db_path.exists():
            db_path.unlink()
        
        # 스키마 재적용
        self._ensure_db_exists()
        logger.info("Database reset completed")


# 싱글톤 인스턴스
_db_instance: Optional[Database] = None


def get_database(db_path: str = "db/algoforge.db") -> Database:
    """
    Database 싱글톤 인스턴스 반환
    
    Args:
        db_path: 데이터베이스 파일 경로
        
    Returns:
        Database: Database 인스턴스
    """
    global _db_instance
    # 테스트 실행 시 별도 DB 사용 (PYTEST_CURRENT_TEST가 설정된 경우)
    test_db_env = os.getenv("ALGOFORGE_TEST_DB_PATH")
    if os.getenv("PYTEST_CURRENT_TEST"):
        # 테스트 케이스별 고유 DB 파일 경로 생성 → 테스트 간 격리
        raw_name = os.getenv("PYTEST_CURRENT_TEST", "")
        test_name = raw_name.split(" ")[0].replace("::", "_").replace("/", "_")
        default_test_path = Path(".pytest_cache") / f"algoforge_{test_name}.db"
        test_db_path = Path(test_db_env) if test_db_env else default_test_path
        test_db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path = str(test_db_path)
        # 새로운 인스턴스를 생성할 때만 파일 초기화
        if (_db_instance is None) or (str(_db_instance.db_path) != db_path):
            if test_db_path.exists():
                test_db_path.unlink()
            _db_instance = Database(db_path)
        return _db_instance
    
    if _db_instance is None or str(_db_instance.db_path) != db_path:
        _db_instance = Database(db_path)
    return _db_instance

