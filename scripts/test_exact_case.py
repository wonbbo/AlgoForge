"""
사용자가 제공한 정확한 케이스 재현 테스트

- 자산: 1000
- 진입가: 0.5207
- 손절가: 0.5217
- 예상 포지션: 20000
- 실제 포지션: 20023
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.db.database import get_database
from engine.core.risk_manager import RiskManager


def test_exact_case():
    """정확한 케이스 재현"""
    print("=" * 80)
    print("사용자 제공 케이스 재현 테스트")
    print("=" * 80)
    
    # 주어진 조건
    balance = 1000
    entry_price = 0.5207
    stop_loss = 0.5217
    risk_percent = 0.02
    
    print(f"\n[주어진 조건]")
    print(f"   자산: ${balance:,.2f}")
    print(f"   진입가: ${entry_price:.4f}")
    print(f"   손절가: ${stop_loss:.4f}")
    print(f"   손실제한: {risk_percent * 100}%")
    
    # 수동 계산
    print(f"\n[예상 계산]")
    initial_risk = abs(entry_price - stop_loss)
    print(f"   초기 리스크: ${initial_risk:.4f}")
    
    risk_limit = balance * risk_percent
    print(f"   리스크 제한: ${risk_limit:.2f}")
    
    expected_position = risk_limit / initial_risk
    print(f"   포지션 크기 (예상): {expected_position:.6f} 계약")
    
    expected_notional = expected_position * entry_price
    print(f"   매수 규모 (예상): ${expected_notional:.2f}")
    
    expected_leverage_raw = expected_notional / balance
    expected_leverage = round(expected_leverage_raw)
    print(f"   레버리지 (예상): {expected_leverage_raw:.2f}x → {expected_leverage}x")
    
    try:
        # DB 연결
        db = get_database()
        
        # RiskManager로 실제 계산
        print(f"\n[실제 계산]")
        risk_manager = RiskManager(
            initial_balance=balance,
            risk_percent=risk_percent,
            risk_reward_ratio=1.5,
            db_conn=db
        )
        
        position_size, risk_calc, leverage = risk_manager.calculate_position_size(
            entry_price, 
            stop_loss
        )
        
        notional_value = position_size * entry_price
        
        print(f"   초기 리스크: ${risk_calc:.4f}")
        print(f"   포지션 크기 (실제): {position_size:.6f} 계약")
        print(f"   매수 규모 (실제): ${notional_value:.2f}")
        print(f"   레버리지 (실제): {int(leverage)}x")
        
        # 차이 분석
        print(f"\n[차이 분석]")
        pos_diff = position_size - expected_position
        notional_diff = notional_value - expected_notional
        leverage_diff = int(leverage) - expected_leverage
        
        print(f"   포지션 차이: {pos_diff:+.6f} 계약")
        print(f"   매수 규모 차이: ${notional_diff:+.2f}")
        print(f"   레버리지 차이: {leverage_diff:+d}x")
        
        # 레버리지 bracket 확인
        print(f"\n[레버리지 Bracket 확인]")
        from engine.utils.leverage_loader import get_max_leverage_for_notional
        
        max_lev_expected = get_max_leverage_for_notional(
            risk_manager.leverage_brackets, 
            expected_notional
        )
        max_lev_actual = get_max_leverage_for_notional(
            risk_manager.leverage_brackets, 
            notional_value
        )
        
        print(f"   예상 매수 규모 ${expected_notional:.2f} → Bracket: {int(max_lev_expected)}x")
        print(f"   실제 매수 규모 ${notional_value:.2f} → Bracket: {int(max_lev_actual)}x")
        
        # 레버리지 제약 확인
        max_notional_allowed = balance * int(max_lev_actual)
        print(f"\n[레버리지 제약 확인]")
        print(f"   현재 잔고: ${balance:,.2f}")
        print(f"   적용 가능 레버리지: {int(max_lev_actual)}x")
        print(f"   최대 매수 가능 규모: ${max_notional_allowed:,.2f}")
        print(f"   실제 매수 규모: ${notional_value:,.2f}")
        
        if notional_value > max_notional_allowed:
            print(f"   [ERROR] 레버리지 제약 위반! ({notional_value:.2f} > {max_notional_allowed:.2f})")
        else:
            print(f"   [OK] 레버리지 제약 준수")
        
        # 상세 디버깅: 레버리지 제약 적용 과정
        print(f"\n[상세 디버깅: 레버리지 제약 적용 과정]")
        
        # 리스크 기반 포지션 (제약 전)
        position_before_constraint = (balance * risk_percent) / initial_risk
        notional_before_constraint = position_before_constraint * entry_price
        
        print(f"   1. 리스크 기반 포지션: {position_before_constraint:.6f} 계약")
        print(f"   2. 리스크 기반 명목가치: ${notional_before_constraint:.2f}")
        
        max_lev_for_risk_based = get_max_leverage_for_notional(
            risk_manager.leverage_brackets,
            notional_before_constraint
        )
        print(f"   3. 해당 bracket: {int(max_lev_for_risk_based)}x")
        
        max_notional_for_bracket = balance * int(max_lev_for_risk_based)
        print(f"   4. Bracket의 최대 매수 가능: ${max_notional_for_bracket:,.2f}")
        
        if notional_before_constraint > max_notional_for_bracket:
            adjusted_position = max_notional_for_bracket / entry_price
            print(f"   5. 제약 적용 → 조정된 포지션: {adjusted_position:.6f} 계약")
        else:
            adjusted_position = position_before_constraint
            print(f"   5. 제약 불필요 → 포지션 유지: {adjusted_position:.6f} 계약")
        
        import math
        floored_position = math.floor(adjusted_position)
        print(f"   6. 내림(floor): {floored_position} 계약")
        
        final_notional = floored_position * entry_price
        final_leverage_raw = final_notional / balance
        final_leverage = round(final_leverage_raw)
        
        print(f"   7. 최종 명목가치: ${final_notional:.2f}")
        print(f"   8. 최종 레버리지 계산: {final_leverage_raw:.2f}x → {final_leverage}x")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_exact_case()
