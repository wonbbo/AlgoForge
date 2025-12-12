"""
SQLite 데이터베이스 연결 및 관리 모듈

이 모듈은 AlgoForge의 SQLite 데이터베이스 연결을 관리합니다.
- WAL 모드 활성화
- 컨텍스트 매니저 기반 연결 관리
- 자동 스키마 초기화
"""

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
        # apps/api/db/database.py -> AlgoForge/db/schema.sql
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        schema_path = project_root / 'db' / 'schema.sql'
        
        logger.info(f"Looking for schema at: {schema_path.absolute()}")
        
        if not schema_path.exists():
            logger.warning(f"Schema file not found: {schema_path}")
            return
        
        # 테이블 존재 여부 확인
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='datasets'"
                )
                table_exists = cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f"Failed to check table existence: {e}")
            table_exists = False
        
        # 테이블이 없으면 스키마 적용
        if not table_exists:
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
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance

