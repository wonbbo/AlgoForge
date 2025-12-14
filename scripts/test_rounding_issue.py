"""
반올림 문제 재현 테스트

자산 1000, 레버리지 10x인데 매수가 10425.9761인 경우를 재현합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.db.database import get_database
from engine.core.risk_manager import RiskManager


def test_rounding_issue():
    """반올림 문제 테스트"""
    print("=" * 70)
    print("반올림 문제 재현 테스트")
    print("=" * 70)
    
    try:
        # DB 연결
        db = get_database()
        
        # 문제 상황 재현
        print("\n[시나리오] 자산 1000, 레버리지 10x 예상, 매수 10425.9761 발생")
        
        # RiskManager 생성
        balance = 1000
        risk_manager = RiskManager(
            initial_balance=balance,
            risk_percent=0.02,
            risk_reward_ratio=1.5,
            db_conn=db
        )
        
        # 여러 가격대 테스트
        test_prices = [
            (50000, 49900, "BTC 50000, SL 49900"),
            (30000, 29900, "BTC 30000, SL 29900"),
            (10000, 9900, "BTC 10000, SL 9900"),
        ]
        
        for entry_price, stop_loss, desc in test_prices:
            print(f"\n{desc}")
            print(f"   진입가: ${entry_price:,.2f}")
            print(f"   손절가: ${stop_loss:,.2f}")
            print(f"   현재 잔고: ${balance:,.2f}")
            
            # 포지션 크기 계산
            position_size, risk, leverage = risk_manager.calculate_position_size(
                entry_price, 
                stop_loss
            )
            
            # 명목가치
            notional_value = position_size * entry_price
            
            # 예상 최대 명목가치 (레버리지 제약)
            from engine.utils.leverage_loader import get_max_leverage_for_notional
            
            # 리스크 기반 포지션 크기 (제약 적용 전)
            risk_based_position = (balance * 0.02) / abs(entry_price - stop_loss)
            risk_based_notional = risk_based_position * entry_price
            
            # 해당 명목가치의 max_leverage
            max_lev = get_max_leverage_for_notional(risk_manager.leverage_brackets, risk_based_notional)
            max_notional = balance * int(max_lev)
            
            print(f"   리스크 기반 포지션: {risk_based_position:.6f} 계약")
            print(f"   리스크 기반 명목가치: ${risk_based_notional:,.2f}")
            print(f"   적용 가능 최대 레버리지: {int(max_lev)}x")
            print(f"   최대 명목가치: ${max_notional:,.2f}")
            print(f"")
            print(f"   → 최종 포지션: {position_size:.6f} 계약")
            print(f"   → 최종 명목가치: ${notional_value:,.2f}")
            print(f"   → 사용 레버리지: {int(leverage)}x")
            
            # 검증
            if notional_value > max_notional:
                print(f"   [ERROR] 명목가치가 한도 초과! ({notional_value:.2f} > {max_notional:.2f})")
            else:
                print(f"   [OK] 레버리지 제약 준수")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_rounding_issue()
