"""
Migration 008: datasets 테이블에 symbol, market_type 컬럼 추가
"""
import sqlite3
from pathlib import Path


def apply_migration():
    db_path = Path(__file__).parent / "algoforge.db"

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(datasets)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'symbol' in columns and 'market_type' in columns:
            print("Migration 008 이미 적용됨.")
            return

        print("datasets 테이블에 symbol, market_type 컬럼 추가 중...")

        if 'symbol' not in columns:
            cursor.execute(
                "ALTER TABLE datasets ADD COLUMN symbol TEXT NOT NULL DEFAULT 'XRPUSDT'"
            )
        if 'market_type' not in columns:
            cursor.execute(
                "ALTER TABLE datasets ADD COLUMN market_type TEXT NOT NULL DEFAULT 'futures_um'"
            )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_datasets_symbol_market_tf "
            "ON datasets(symbol, market_type, timeframe)"
        )

        conn.commit()
        print("[SUCCESS] Migration 008 적용 완료")

        cursor.execute(
            "SELECT dataset_id, name, symbol, market_type, timeframe FROM datasets"
        )
        for row in cursor.fetchall():
            print(f"  dataset_id={row[0]} name={row[1]} symbol={row[2]} "
                  f"market_type={row[3]} timeframe={row[4]}")

    except Exception as e:
        print(f"[ERROR] Migration 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    apply_migration()
