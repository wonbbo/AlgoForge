"""
상세한 반올림 문제 디버깅
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 모듈 리로드 (캐시 방지)
import importlib
import engine.core.risk_manager
importlib.reload(engine.core.risk_manager)

from apps.api.db.database import get_database
from engine.core.risk_manager import RiskManager


def test_detailed():
    """상세 테스트"""
    print("=" * 70)
    print("상세한 포지션 크기 계산 테스트")
    print("=" * 70)
    
    try:
        # DB 연결
        db = get_database()
        
        # 테스트: 잔고 1000, BTC 50000
        balance = 1000
        entry_price = 50000
        stop_loss = 49900
        
        print(f"\n[테스트 조건]")
        print(f"   잔고: ${balance:,.0f}")
        print(f"   진입가: ${entry_price:,.0f}")
        print(f"   손절가: ${stop_loss:,.0f}")
        
        # RiskManager 생성
        risk_manager = RiskManager(
            initial_balance=balance,
            risk_percent=0.02,
            risk_reward_ratio=1.5,
            db_conn=db
        )
        
        print(f"\n[계산 과정]")
        
        # 리스크 계산
        risk = abs(entry_price - stop_loss)
        print(f"   1. 리스크: ${risk:.2f}")
        
        # 리스크 기반 포지션
        position_raw = (balance * 0.02) / risk
        print(f"   2. 리스크 기반 포지션: {position_raw:.6f} 계약")
        
        # 명목가치
        notional_raw = position_raw * entry_price
        print(f"   3. 리스크 기반 명목가치: ${notional_raw:,.2f}")
        
        # 레버리지 bracket 확인
        from engine.utils.leverage_loader import get_max_leverage_for_notional
        max_lev = get_max_leverage_for_notional(risk_manager.leverage_brackets, notional_raw)
        print(f"   4. 적용 bracket: {int(max_lev)}x")
        
        # 최대 명목가치
        max_notional = balance * int(max_lev)
        print(f"   5. 최대 명목가치: ${max_notional:,.2f}")
        
        # 레버리지 제약 적용 후
        if notional_raw > max_notional:
            adjusted_position = max_notional / entry_price
            print(f"   6. 제약 적용 → 포지션: {adjusted_position:.6f} 계약")
        else:
            adjusted_position = position_raw
            print(f"   6. 제약 불필요 → 포지션: {adjusted_position:.6f} 계약")
        
        # 내림
        import math
        floored = math.floor(adjusted_position)
        print(f"   7. 내림(floor): {floored} 계약")
        
        # 0인 경우 1 계약 검증
        if floored == 0:
            print(f"\n[1 계약 검증]")
            notional_one = 1.0 * entry_price
            print(f"   1 계약 명목가치: ${notional_one:,.2f}")
            
            max_lev_one = get_max_leverage_for_notional(risk_manager.leverage_brackets, notional_one)
            print(f"   1 계약 bracket: {int(max_lev_one)}x")
            
            required_margin = notional_one / int(max_lev_one)
            print(f"   필요 증거금: ${required_margin:,.2f}")
            print(f"   현재 잔고: ${balance:,.2f}")
            
            if required_margin <= balance:
                print(f"   → 1 계약 진입 가능!")
                floored = 1
            else:
                print(f"   → 1 계약 진입 불가")
        
        print(f"\n[최종 결과]")
        
        # 실제 함수 호출
        position_size, risk_calc, leverage = risk_manager.calculate_position_size(
            entry_price, 
            stop_loss
        )
        
        notional_final = position_size * entry_price
        
        print(f"   포지션 크기: {position_size:.0f} 계약")
        print(f"   명목가치: ${notional_final:,.2f}")
        print(f"   레버리지: {int(leverage)}x")
        print(f"   리스크: ${risk_calc:.2f}")
        
        # 검증
        if position_size == 0:
            print(f"\n   [WARNING] 포지션이 0입니다!")
        elif notional_final <= balance * leverage:
            print(f"\n   [OK] 레버리지 제약 준수")
        else:
            print(f"\n   [ERROR] 레버리지 제약 위반!")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_detailed()
