"""
Migration 009: run_datasets 정션 테이블 추가 (멀티 타임프레임 지원)
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
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='run_datasets'"
        )
        if cursor.fetchone():
            print("Migration 009 이미 적용됨.")
            return

        print("run_datasets 정션 테이블 생성 중...")
        cursor.executescript("""
            CREATE TABLE run_datasets (
                run_id INTEGER NOT NULL,
                dataset_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                PRIMARY KEY (run_id, role),
                UNIQUE (run_id, dataset_id, role),
                FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
                FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id) ON DELETE RESTRICT
            );
            CREATE INDEX idx_run_datasets_run ON run_datasets(run_id);
            CREATE INDEX idx_run_datasets_dataset ON run_datasets(dataset_id);
        """)

        # 기존 runs row를 'base' role로 복제
        cursor.execute("""
            INSERT OR IGNORE INTO run_datasets (run_id, dataset_id, role)
            SELECT run_id, dataset_id, 'base' FROM runs WHERE dataset_id IS NOT NULL
        """)
        backfilled = cursor.rowcount

        conn.commit()
        print(f"[SUCCESS] Migration 009 적용 완료 (기존 runs {backfilled}건 base로 백필)")

    except Exception as e:
        print(f"[ERROR] Migration 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    apply_migration()
