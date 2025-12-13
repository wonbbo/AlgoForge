"""
DB 마이그레이션 적용 스크립트
"""
import sqlite3
from pathlib import Path

def apply_migration():
    """진행률 컬럼 추가 마이그레이션 적용"""
    db_path = Path(__file__).parent / "algoforge.db"
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        print("스키마를 새로 생성합니다.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 이미 컬럼이 있는지 확인
        cursor.execute("PRAGMA table_info(runs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'progress_percent' in columns:
            print("마이그레이션이 이미 적용되어 있습니다.")
            return
        
        print("진행률 컬럼을 추가합니다...")
        
        # 마이그레이션 적용
        cursor.execute("ALTER TABLE runs ADD COLUMN progress_percent REAL DEFAULT 0")
        cursor.execute("ALTER TABLE runs ADD COLUMN processed_bars INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE runs ADD COLUMN total_bars INTEGER DEFAULT 0")
        
        conn.commit()
        print("[SUCCESS] 마이그레이션 적용 완료!")
        
    except Exception as e:
        print(f"[ERROR] 마이그레이션 실패: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migration()

