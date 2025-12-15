"""
데이터베이스 초기화 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.db.database import get_database


def reset_database():
    """데이터베이스 초기화"""
    print("=" * 60)
    print("  데이터베이스 초기화")
    print("=" * 60)
    print()
    print("[WARNING] 모든 데이터가 삭제됩니다!")
    response = input("계속하시겠습니까? (y/N): ")
    
    if response.lower() != 'y':
        print("[CANCEL] 초기화를 취소했습니다.")
        return False
    
    try:
        db = get_database()
        db.reset_database()
        print("[OK] 데이터베이스가 초기화되었습니다.")
        print("[OK] 스키마가 적용되었습니다.")
        return True
    except Exception as e:
        print(f"[ERROR] 초기화 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = reset_database()
    
    print()
    if success:
        print("[SUCCESS] 초기화가 완료되었습니다!")
        print("다음 단계: python scripts\\migrate_leverage_data.py")
    else:
        print("[FAILED] 초기화가 실패했습니다.")
        sys.exit(1)

