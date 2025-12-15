"""
indicators 테이블 마이그레이션 적용 스크립트
"""
import sqlite3
from pathlib import Path

def apply_indicators_migration():
    """indicators 테이블 추가 마이그레이션 적용"""
    db_path = Path(__file__).parent / "algoforge.db"
    migration_file = Path(__file__).parent / "migrations" / "002_add_indicators_table.sql"
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        print("먼저 schema.sql로 데이터베이스를 생성해주세요.")
        return False
    
    if not migration_file.exists():
        print(f"Migration file not found: {migration_file}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # indicators 테이블이 이미 있는지 확인
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='indicators'"
        )
        
        if cursor.fetchone():
            print("indicators 테이블이 이미 존재합니다.")
            
            # 데이터 개수 확인
            cursor.execute("SELECT COUNT(*) FROM indicators")
            count = cursor.fetchone()[0]
            print(f"현재 등록된 지표 수: {count}개")
            return True
        
        print("indicators 테이블을 생성합니다...")
        
        # 마이그레이션 SQL 파일 읽기 및 실행
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # 여러 SQL 문장을 실행
        cursor.executescript(migration_sql)
        
        conn.commit()
        
        # 결과 확인
        cursor.execute("SELECT COUNT(*) FROM indicators")
        count = cursor.fetchone()[0]
        
        print("[SUCCESS] indicators 테이블 생성 완료!")
        print(f"기본 내장 지표 {count}개가 등록되었습니다.")
        
        # 등록된 지표 목록 출력
        cursor.execute("SELECT type, name, category FROM indicators ORDER BY category, name")
        print("\n등록된 지표 목록:")
        for row in cursor.fetchall():
            print(f"  - {row[0]:15s} | {row[1]:20s} | {row[2]}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 마이그레이션 실패: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = apply_indicators_migration()
    if not success:
        exit(1)

