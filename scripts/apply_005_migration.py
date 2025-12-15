"""
005 마이그레이션 적용: trades 테이블에 balance_at_entry 컬럼 추가
"""

import sqlite3
from pathlib import Path

# 프로젝트 루트 경로
project_root = Path(__file__).parent.parent

# DB 경로
db_path = project_root / 'db' / 'algoforge.db'

# 마이그레이션 파일 경로
migration_path = project_root / 'db' / 'migrations' / '005_add_balance_at_entry_to_trades.sql'

print(f"DB 경로: {db_path}")
print(f"마이그레이션 파일: {migration_path}")

# 마이그레이션 실행
with open(migration_path, 'r', encoding='utf-8') as f:
    migration_sql = f.read()

conn = sqlite3.connect(db_path)
try:
    conn.executescript(migration_sql)
    conn.commit()
    print("\n[SUCCESS] balance_at_entry 컬럼 추가 완료!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("\n[INFO] balance_at_entry 컬럼이 이미 존재합니다.")
    else:
        print(f"\n[ERROR] 마이그레이션 실패: {e}")
        raise
finally:
    conn.close()
