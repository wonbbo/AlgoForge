"""
레버리지 로직 테스트 스크립트

수정된 레버리지 계산 로직이 올바르게 작동하는지 검증합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.db.database import get_database
from engine.core.risk_manager import RiskManager
from engine.utils.leverage_loader import load_leverage_brackets_from_db


def test_leverage_logic():
    """레버리지 로직 테스트"""
    print("=" * 70)
    print("레버리지 로직 테스트")
    print("=" * 70)
    
    try:
        # DB 연결
        db = get_database()
        
        # 레버리지 테이블 로드
        print("\n[1단계] 레버리지 테이블 로드")
        brackets = load_leverage_brackets_from_db(db)
        print(f"   로드된 bracket 개수: {len(brackets)}")
        
        for i, bracket in enumerate(brackets):
            print(f"   Bracket {i+1}: ${bracket.bracket_min:,.0f} ~ ${bracket.bracket_max:,.0f} -> {int(bracket.max_leverage)}x")
        
        # 테스트 시나리오
        test_cases = [
            # (초기잔고, 진입가, 손절가, 설명)
            (1000, 50000, 49000, "잔고 $1,000, BTC $50,000 진입"),
            (10000, 50000, 49000, "잔고 $10,000, BTC $50,000 진입"),
            (100000, 50000, 49000, "잔고 $100,000, BTC $50,000 진입"),
            (5000, 50000, 48000, "잔고 $5,000, BTC $50,000 진입 (큰 리스크)"),
        ]
        
        print("\n[2단계] 테스트 시나리오 실행")
        print("-" * 70)
        
        for i, (balance, entry_price, stop_loss, desc) in enumerate(test_cases, 1):
            print(f"\n테스트 케이스 {i}: {desc}")
            print(f"   초기 잔고: ${balance:,.0f}")
            print(f"   진입가: ${entry_price:,.0f}")
            print(f"   손절가: ${stop_loss:,.0f}")
            
            # RiskManager 생성
            risk_manager = RiskManager(
                initial_balance=balance,
                risk_percent=0.02,
                risk_reward_ratio=1.5,
                db_conn=db
            )
            
            # 포지션 크기 및 레버리지 계산
            position_size, risk, leverage = risk_manager.calculate_position_size(
                entry_price, 
                stop_loss
            )
            
            # 명목가치 계산
            notional_value = position_size * entry_price
            
            # 결과 출력
            print(f"   → 포지션 크기: {position_size:.4f} 계약")
            print(f"   → 명목가치: ${notional_value:,.2f}")
            print(f"   → 사용 레버리지: {int(leverage)}x")
            print(f"   → 리스크: ${risk:.2f}")
            print(f"   → 증거금: ${notional_value/leverage:,.2f}")
            
            # 검증
            if notional_value / balance > leverage:
                print(f"   [!] 경고: 레버리지가 실제보다 낮게 계산됨")
            else:
                print(f"   [OK] 레버리지가 올바르게 계산됨")
        
        print("\n" + "=" * 70)
        print("[SUCCESS] 모든 테스트 완료")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_leverage_logic()
    
    if not success:
        sys.exit(1)
