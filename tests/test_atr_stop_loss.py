"""
ATR 기반 손절가 계산 테스트
"""

import sys
from pathlib import Path

# engine 모듈 import를 위한 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.models.bar import Bar
from engine.utils.indicators import IndicatorCalculator
from engine.utils.strategy_parser import StrategyParser


def test_atr_calculation():
    """ATR 계산 테스트"""
    
    # 테스트 데이터 생성 (변동성이 있는 데이터)
    bars = [
        Bar(timestamp=1000, open=100, high=105, low=95, close=102, volume=1000, direction=1),
        Bar(timestamp=1005, open=102, high=108, low=100, close=107, volume=1100, direction=1),
        Bar(timestamp=1010, open=107, high=112, low=105, close=110, volume=1200, direction=1),
        Bar(timestamp=1015, open=110, high=115, low=108, close=112, volume=1300, direction=1),
        Bar(timestamp=1020, open=112, high=118, low=110, close=115, volume=1400, direction=1),
    ]
    
    # Indicator Calculator 생성
    calc = IndicatorCalculator(bars)
    
    # ATR 계산
    calc.calculate_atr("atr_14", period=3)
    
    # ATR 값 확인
    for i, bar in enumerate(bars):
        atr_value = calc.get_value("atr_14", i)
        print(f"Bar {i}: High={bar.high}, Low={bar.low}, Close={bar.close}, ATR={atr_value:.2f}")
        
        # ATR 값이 양수여야 함
        assert atr_value >= 0, f"ATR 값은 0 이상이어야 합니다: {atr_value}"
    
    print("PASS: ATR calculation test")


def test_atr_based_stop_loss():
    """ATR 기반 손절가 계산 테스트"""
    
    # 테스트 데이터 생성
    bars = [
        Bar(timestamp=1000, open=100, high=105, low=95, close=102, volume=1000, direction=1),
        Bar(timestamp=1005, open=102, high=108, low=100, close=107, volume=1100, direction=1),
        Bar(timestamp=1010, open=107, high=112, low=105, close=110, volume=1200, direction=1),
        Bar(timestamp=1015, open=110, high=115, low=108, close=112, volume=1300, direction=1),
        Bar(timestamp=1020, open=112, high=118, low=110, close=115, volume=1400, direction=1),
    ]
    
    # 전략 정의 (ATR 기반 손절)
    strategy_definition = {
        "indicators": [
            {
                "id": "atr_14",
                "type": "atr",
                "params": {
                    "period": 3
                }
            }
        ],
        "entry": {
            "long": {
                "and": [
                    {
                        "left": {"price": "close"},
                        "op": ">",
                        "right": {"value": 100}
                    }
                ]
            },
            "short": {
                "and": []
            }
        },
        "stop_loss": {
            "type": "atr_based",
            "atr_indicator_id": "atr_14",
            "multiplier": 2.0
        }
    }
    
    # 파서 생성
    parser = StrategyParser(strategy_definition, bars)
    strategy_func = parser.create_strategy_function()
    
    # 테스트: 각 봉에서 손절가 계산
    print("\nATR 기반 손절가 계산:")
    for i, bar in enumerate(bars):
        result = strategy_func(bar)
        if result:
            atr_value = parser.indicator_calc.get_value("atr_14", i)
            print(f"Bar {i}: Close={bar.close:.2f}, ATR={atr_value:.2f}, SL={result['stop_loss']:.2f}")
            
            # LONG 포지션의 손절가는 진입가보다 낮아야 함
            assert result['direction'] == 'LONG'
            assert result['stop_loss'] < bar.close, \
                f"LONG 손절가는 진입가보다 낮아야 합니다: SL={result['stop_loss']}, Entry={bar.close}"
            
            # 손절가가 대략적으로 entry - (ATR * 2)와 일치해야 함
            expected_sl = bar.close - (atr_value * 2.0)
            assert abs(result['stop_loss'] - expected_sl) < 0.01, \
                f"손절가 계산 오류: expected={expected_sl:.2f}, actual={result['stop_loss']:.2f}"
    
    print("PASS: ATR based stop loss test")


def test_atr_based_stop_loss_short():
    """ATR 기반 손절가 계산 테스트 (숏 포지션)"""
    
    # 테스트 데이터 생성
    bars = [
        Bar(timestamp=1000, open=100, high=105, low=95, close=102, volume=1000, direction=1),
        Bar(timestamp=1005, open=102, high=108, low=100, close=107, volume=1100, direction=1),
        Bar(timestamp=1010, open=107, high=112, low=105, close=110, volume=1200, direction=1),
        Bar(timestamp=1015, open=110, high=115, low=108, close=112, volume=1300, direction=1),
        Bar(timestamp=1020, open=112, high=118, low=110, close=115, volume=1400, direction=1),
    ]
    
    # 전략 정의 (ATR 기반 손절, 숏 포지션)
    strategy_definition = {
        "indicators": [
            {
                "id": "atr_14",
                "type": "atr",
                "params": {
                    "period": 3
                }
            }
        ],
        "entry": {
            "long": {
                "and": []
            },
            "short": {
                "and": [
                    {
                        "left": {"price": "close"},
                        "op": ">",
                        "right": {"value": 100}
                    }
                ]
            }
        },
        "stop_loss": {
            "type": "atr_based",
            "atr_indicator_id": "atr_14",
            "multiplier": 2.0
        }
    }
    
    # 파서 생성
    parser = StrategyParser(strategy_definition, bars)
    strategy_func = parser.create_strategy_function()
    
    # 테스트: 각 봉에서 손절가 계산
    print("\nATR 기반 손절가 계산 (SHORT):")
    for i, bar in enumerate(bars):
        result = strategy_func(bar)
        if result:
            atr_value = parser.indicator_calc.get_value("atr_14", i)
            print(f"Bar {i}: Close={bar.close:.2f}, ATR={atr_value:.2f}, SL={result['stop_loss']:.2f}")
            
            # SHORT 포지션의 손절가는 진입가보다 높아야 함
            assert result['direction'] == 'SHORT'
            assert result['stop_loss'] > bar.close, \
                f"SHORT 손절가는 진입가보다 높아야 합니다: SL={result['stop_loss']}, Entry={bar.close}"
            
            # 손절가가 대략적으로 entry + (ATR * 2)와 일치해야 함
            expected_sl = bar.close + (atr_value * 2.0)
            assert abs(result['stop_loss'] - expected_sl) < 0.01, \
                f"손절가 계산 오류: expected={expected_sl:.2f}, actual={result['stop_loss']:.2f}"
    
    print("PASS: ATR based stop loss test (SHORT)")


def test_atr_different_multipliers():
    """다양한 ATR multiplier 테스트"""
    
    # 테스트 데이터 생성
    bars = [
        Bar(timestamp=1000, open=100, high=105, low=95, close=102, volume=1000, direction=1),
        Bar(timestamp=1005, open=102, high=108, low=100, close=107, volume=1100, direction=1),
        Bar(timestamp=1010, open=107, high=112, low=105, close=110, volume=1200, direction=1),
    ]
    
    multipliers = [1.0, 1.5, 2.0, 2.5, 3.0]
    
    print("\n다양한 ATR multiplier 테스트:")
    for multiplier in multipliers:
        strategy_definition = {
            "indicators": [
                {
                    "id": "atr_14",
                    "type": "atr",
                    "params": {"period": 2}
                }
            ],
            "entry": {
                "long": {
                    "and": [
                        {
                            "left": {"price": "close"},
                            "op": ">",
                            "right": {"value": 100}
                        }
                    ]
                },
                "short": {"and": []}
            },
            "stop_loss": {
                "type": "atr_based",
                "atr_indicator_id": "atr_14",
                "multiplier": multiplier
            }
        }
        
        parser = StrategyParser(strategy_definition, bars)
        strategy_func = parser.create_strategy_function()
        
        result = strategy_func(bars[-1])
        if result:
            atr_value = parser.indicator_calc.get_value("atr_14", len(bars) - 1)
            expected_sl = bars[-1].close - (atr_value * multiplier)
            
            print(f"  Multiplier={multiplier}: Entry={bars[-1].close:.2f}, ATR={atr_value:.2f}, SL={result['stop_loss']:.2f}")
            
            assert abs(result['stop_loss'] - expected_sl) < 0.01, \
                f"Multiplier={multiplier} 손절가 계산 오류"
    
    print("PASS: ATR different multipliers test")


def test_atr_true_range_calculation():
    """True Range 계산 검증 테스트"""
    
    # True Range 계산을 수동으로 검증할 수 있는 간단한 데이터
    bars = [
        Bar(timestamp=1000, open=100, high=110, low=90, close=105, volume=1000, direction=1),
        Bar(timestamp=1005, open=105, high=115, low=100, close=112, volume=1100, direction=1),
        Bar(timestamp=1010, open=112, high=120, low=108, close=115, volume=1200, direction=1),
    ]
    
    calc = IndicatorCalculator(bars)
    calc.calculate_atr("atr_test", period=2)
    
    # 첫 번째 봉의 TR = high - low = 110 - 90 = 20
    # 두 번째 봉의 TR = max(115-100=15, |115-105|=10, |100-105|=5) = 15
    # 세 번째 봉의 TR = max(120-108=12, |120-112|=8, |108-112|=4) = 12
    
    print("\nTrue Range 계산 검증:")
    for i, bar in enumerate(bars):
        atr_value = calc.get_value("atr_test", i)
        print(f"Bar {i}: ATR={atr_value:.2f}")
    
    # 세 번째 봉의 ATR은 (15 + 12) / 2 = 13.5여야 함
    atr_bar2 = calc.get_value("atr_test", 2)
    expected_atr = (15 + 12) / 2
    assert abs(atr_bar2 - expected_atr) < 0.01, \
        f"ATR 계산 오류: expected={expected_atr:.2f}, actual={atr_bar2:.2f}"
    
    print("PASS: True Range calculation test")


if __name__ == "__main__":
    print("=" * 60)
    print("ATR 기반 손절가 테스트 시작")
    print("=" * 60)
    
    print("\n[Test 1] ATR 계산")
    print("-" * 60)
    test_atr_calculation()
    
    print("\n[Test 2] ATR 기반 손절가 (LONG)")
    print("-" * 60)
    test_atr_based_stop_loss()
    
    print("\n[Test 3] ATR 기반 손절가 (SHORT)")
    print("-" * 60)
    test_atr_based_stop_loss_short()
    
    print("\n[Test 4] 다양한 ATR multiplier")
    print("-" * 60)
    test_atr_different_multipliers()
    
    print("\n[Test 5] True Range 계산 검증")
    print("-" * 60)
    test_atr_true_range_calculation()
    
    print("\n" + "=" * 60)
    print("ALL ATR TESTS PASSED!")
    print("=" * 60)

