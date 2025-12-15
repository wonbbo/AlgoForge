"""
레버리지 CSV 데이터를 DB로 마이그레이션하는 스크립트
"""
import sys
import csv
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.db.database import get_database
from apps.api.db.repositories import LeverageBracketRepository


def migrate_leverage_data():
    """
    ac_leverage.csv 파일을 읽어 DB에 저장
    """
    # CSV 파일 경로
    csv_path = project_root / "db" / "ac_leverage.csv"
    
    if not csv_path.exists():
        print(f"[ERROR] CSV 파일을 찾을 수 없습니다: {csv_path}")
        return False
    
    print(f"[INFO] CSV 파일 읽기: {csv_path}")
    
    # CSV 파일 읽기
    brackets = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    bracket = {
                        'bracket_min': float(row['bracket_min']),
                        'bracket_max': float(row['bracket_max']),
                        'max_leverage': float(row['max_leverage']),
                        'm_margin_rate': float(row['m_margin_rate']),
                        'm_amount': float(row['m_amount'])
                    }
                    brackets.append(bracket)
                except (ValueError, KeyError) as e:
                    # 빈 줄이나 잘못된 데이터는 스킵
                    continue
        
        print(f"[OK] CSV 파일에서 {len(brackets)}개의 레버리지 구간을 읽었습니다.")
        
    except Exception as e:
        print(f"[ERROR] CSV 파일 읽기 실패: {str(e)}")
        return False
    
    if not brackets:
        print("[WARNING] 유효한 레버리지 구간 데이터가 없습니다.")
        return False
    
    # DB에 저장
    try:
        db = get_database()
        repo = LeverageBracketRepository(db)
        
        # 기존 데이터 확인
        existing_count = repo.count()
        
        if existing_count > 0:
            print(f"[WARNING] DB에 이미 {existing_count}개의 레버리지 구간이 존재합니다.")
            response = input("기존 데이터를 삭제하고 새로 입력하시겠습니까? (y/N): ")
            
            if response.lower() == 'y':
                deleted = repo.delete_all()
                print(f"[DELETE] 기존 {deleted}개의 레버리지 구간을 삭제했습니다.")
            else:
                print("[CANCEL] 마이그레이션을 취소했습니다.")
                return False
        
        # 대량 생성
        created_count = repo.bulk_create(brackets)
        print(f"[OK] {created_count}개의 레버리지 구간을 DB에 저장했습니다.")
        
        # 검증: 저장된 데이터 확인
        saved_brackets = repo.get_all()
        print(f"\n[INFO] 저장된 레버리지 구간:")
        print(f"{'구간(USDT)':<25} {'최대 레버리지':<15} {'유지증거금률':<15}")
        print("-" * 60)
        
        for bracket in saved_brackets[:5]:  # 처음 5개만 출력
            range_str = f"{bracket['bracket_min']:,.0f} ~ {bracket['bracket_max']:,.0f}"
            print(f"{range_str:<25} {bracket['max_leverage']:<15.0f}x {bracket['m_margin_rate']:<15.4f}")
        
        if len(saved_brackets) > 5:
            print(f"... 외 {len(saved_brackets) - 5}개")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] DB 저장 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  레버리지 데이터 마이그레이션")
    print("=" * 60)
    print()
    
    success = migrate_leverage_data()
    
    print()
    if success:
        print("[SUCCESS] 마이그레이션이 완료되었습니다!")
    else:
        print("[FAILED] 마이그레이션이 실패했습니다.")
        sys.exit(1)

