"""
Migration 006 적용 스크립트

trades 테이블에 leverage 컬럼을 추가합니다.
"""

import sqlite3
from pathlib import Path
import sys

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def apply_migration():
    """Migration 006 적용: trades 테이블에 leverage 컬럼 추가"""
    db_path = project_root / "db" / "algoforge.db"
    migration_path = project_root / "db" / "migrations" / "006_add_leverage_to_trades.sql"
    
    if not db_path.exists():
        print(f"[ERROR] 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return False
    
    if not migration_path.exists():
        print(f"[ERROR] Migration 파일을 찾을 수 없습니다: {migration_path}")
        return False
    
    print(f"[DB] 경로: {db_path}")
    print(f"[Migration] 경로: {migration_path}")
    
    try:
        # Migration SQL 읽기
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # DB 연결 및 실행
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 현재 테이블 구조 확인
        cursor.execute("PRAGMA table_info(trades)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'leverage' in columns:
            print("[!] leverage 컬럼이 이미 존재합니다. Migration을 스킵합니다.")
            conn.close()
            return True
        
        print("[+] Migration 실행 중...")
        
        # Migration 실행
        cursor.executescript(migration_sql)
        conn.commit()
        
        # 확인
        cursor.execute("PRAGMA table_info(trades)")
        columns_after = [row[1] for row in cursor.fetchall()]
        
        if 'leverage' in columns_after:
            print("[OK] Migration이 성공적으로 적용되었습니다!")
            print("    trades 테이블에 leverage 컬럼이 추가되었습니다.")
        else:
            print("[FAIL] Migration 적용에 실패했습니다.")
            conn.close()
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Migration 006: trades 테이블에 leverage 컬럼 추가")
    print("=" * 60)
    
    success = apply_migration()
    
    print("=" * 60)
    if success:
        print("[SUCCESS] Migration 완료!")
    else:
        print("[FAIL] Migration 실패!")
        sys.exit(1)
