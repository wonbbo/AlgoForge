"""
OHLCV 조건을 사용하는 전략 파서 테스트
"""

import sys
from pathlib import Path

# engine 모듈 import를 위한 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.models.bar import Bar
from engine.utils.strategy_parser import StrategyParser


def test_ohlcv_condition_close_greater_than_ema():
    """Close > EMA 조건 테스트"""
    
    # 테스트 데이터 생성 (timestamp는 순차적인 정수, direction은 봉 방향)
    bars = [
        Bar(timestamp=1000, open=100, high=105, low=95, close=102, volume=1000, direction=1),
        Bar(timestamp=1005, open=102, high=107, low=100, close=105, volume=1100, direction=1),
        Bar(timestamp=1010, open=105, high=110, low=103, close=108, volume=1200, direction=1),
        Bar(timestamp=1015, open=108, high=112, low=106, close=110, volume=1300, direction=1),
        Bar(timestamp=1020, open=110, high=115, low=108, close=112, volume=1400, direction=1),
    ]
    
    # 전략 정의 (Close > EMA(3))
    strategy_definition = {
        "indicators": [
            {
                "id": "ema_3",
                "type": "ema",
                "params": {
                    "source": "close",
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
                        "right": {"ref": "ema_3"}
                    }
                ]
            },
            "short": {
                "and": []
            }
        },
        "stop_loss": {
            "type": "fixed_percent",
            "percent": 2.0
        }
    }
    
    # 파서 생성
    parser = StrategyParser(strategy_definition, bars)
    strategy_func = parser.create_strategy_function()
    
    # 테스트: 각 봉에서 조건 평가
    for i, bar in enumerate(bars):
        result = strategy_func(bar)
        print(f"Bar {i}: close={bar.close:.2f}, result={result}")
    
    print("PASS: Close > EMA condition test")


def test_ohlcv_condition_volume_greater_than_average():
    """Volume > 평균 Volume 조건 테스트"""
    
    # 테스트 데이터 생성
    bars = [
        Bar(timestamp=1000, open=100, high=105, low=95, close=102, volume=1000, direction=1),
        Bar(timestamp=1005, open=102, high=107, low=100, close=105, volume=1100, direction=1),
        Bar(timestamp=1010, open=105, high=110, low=103, close=108, volume=1200, direction=1),
        Bar(timestamp=1015, open=108, high=112, low=106, close=110, volume=2000, direction=1),  # 볼륨 급증
        Bar(timestamp=1020, open=110, high=115, low=108, close=112, volume=2500, direction=1),  # 볼륨 급증
    ]
    
    # 전략 정의 (Volume > SMA(Volume, 3))
    strategy_definition = {
        "indicators": [
            {
                "id": "sma_volume",
                "type": "sma",
                "params": {
                    "source": "volume",
                    "period": 3
                }
            }
        ],
        "entry": {
            "long": {
                "and": [
                    {
                        "left": {"price": "volume"},
                        "op": ">",
                        "right": {"ref": "sma_volume"}
                    }
                ]
            },
            "short": {
                "and": []
            }
        },
        "stop_loss": {
            "type": "fixed_percent",
            "percent": 2.0
        }
    }
    
    # 파서 생성
    parser = StrategyParser(strategy_definition, bars)
    strategy_func = parser.create_strategy_function()
    
    # 테스트: 각 봉에서 조건 평가
    for i, bar in enumerate(bars):
        result = strategy_func(bar)
        print(f"Bar {i}: volume={bar.volume}, result={result}")
    
    print("PASS: Volume > average Volume condition test")


def test_ohlcv_condition_combined():
    """복합 조건 테스트: Close > EMA AND Volume > 평균"""
    
    # 테스트 데이터 생성
    bars = [
        Bar(timestamp=1000, open=100, high=105, low=95, close=102, volume=1000, direction=1),
        Bar(timestamp=1005, open=102, high=107, low=100, close=105, volume=1100, direction=1),
        Bar(timestamp=1010, open=105, high=110, low=103, close=108, volume=1200, direction=1),
        Bar(timestamp=1015, open=108, high=112, low=106, close=110, volume=2000, direction=1),
        Bar(timestamp=1020, open=110, high=115, low=108, close=112, volume=2500, direction=1),
    ]
    
    # 전략 정의 (Close > EMA AND Volume > 평균)
    strategy_definition = {
        "indicators": [
            {
                "id": "ema_3",
                "type": "ema",
                "params": {
                    "source": "close",
                    "period": 3
                }
            },
            {
                "id": "sma_volume",
                "type": "sma",
                "params": {
                    "source": "volume",
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
                        "right": {"ref": "ema_3"}
                    },
                    {
                        "left": {"price": "volume"},
                        "op": ">",
                        "right": {"ref": "sma_volume"}
                    }
                ]
            },
            "short": {
                "and": []
            }
        },
        "stop_loss": {
            "type": "fixed_percent",
            "percent": 2.0
        }
    }
    
    # 파서 생성
    parser = StrategyParser(strategy_definition, bars)
    strategy_func = parser.create_strategy_function()
    
    # 테스트: 각 봉에서 조건 평가
    for i, bar in enumerate(bars):
        result = strategy_func(bar)
        print(f"Bar {i}: close={bar.close:.2f}, volume={bar.volume}, result={result}")
    
    print("PASS: Combined condition test")


def test_ohlcv_condition_cross_above():
    """Close가 EMA를 상향 돌파하는 조건 테스트"""
    
    # 테스트 데이터 생성 (close가 EMA를 돌파하는 시나리오)
    bars = [
        Bar(timestamp=1000, open=100, high=105, low=95, close=98, volume=1000, direction=-1),   # close < ema
        Bar(timestamp=1005, open=98, high=103, low=96, close=99, volume=1100, direction=1),    # close < ema
        Bar(timestamp=1010, open=99, high=104, low=97, close=102, volume=1200, direction=1),   # close > ema (cross!)
        Bar(timestamp=1015, open=102, high=107, low=100, close=105, volume=1300, direction=1),
        Bar(timestamp=1020, open=105, high=110, low=103, close=108, volume=1400, direction=1),
    ]
    
    # 전략 정의 (Close cross_above EMA)
    strategy_definition = {
        "indicators": [
            {
                "id": "ema_3",
                "type": "ema",
                "params": {
                    "source": "close",
                    "period": 3
                }
            }
        ],
        "entry": {
            "long": {
                "and": [
                    {
                        "left": {"price": "close"},
                        "op": "cross_above",
                        "right": {"ref": "ema_3"}
                    }
                ]
            },
            "short": {
                "and": []
            }
        },
        "stop_loss": {
            "type": "fixed_percent",
            "percent": 2.0
        }
    }
    
    # 파서 생성
    parser = StrategyParser(strategy_definition, bars)
    strategy_func = parser.create_strategy_function()
    
    # 테스트: 각 봉에서 조건 평가
    for i, bar in enumerate(bars):
        result = strategy_func(bar)
        ema_value = parser.indicator_calc.get_value("ema_3", i)
        cross_indicator = "<-- CROSS!" if result is not None else ""
        print(f"Bar {i}: close={bar.close:.2f}, ema={ema_value:.2f}, result={result} {cross_indicator}")
    
    print("PASS: Close cross_above EMA condition test")


def test_ohlcv_all_fields():
    """모든 OHLCV 필드 테스트"""
    
    # 테스트 데이터
    bars = [
        Bar(timestamp=1000, open=100, high=105, low=95, close=102, volume=1000, direction=1),
        Bar(timestamp=1005, open=102, high=107, low=100, close=105, volume=1100, direction=1),
    ]
    
    # 전략 정의 (각 OHLCV 필드 테스트)
    strategy_definition = {
        "indicators": [],
        "entry": {
            "long": {
                "and": [
                    {
                        "left": {"price": "open"},
                        "op": ">",
                        "right": {"value": 90}
                    },
                    {
                        "left": {"price": "high"},
                        "op": ">",
                        "right": {"value": 100}
                    },
                    {
                        "left": {"price": "low"},
                        "op": ">",
                        "right": {"value": 90}
                    },
                    {
                        "left": {"price": "close"},
                        "op": ">",
                        "right": {"value": 95}
                    },
                    {
                        "left": {"price": "volume"},
                        "op": ">",
                        "right": {"value": 500}
                    }
                ]
            },
            "short": {
                "and": []
            }
        },
        "stop_loss": {
            "type": "fixed_percent",
            "percent": 2.0
        }
    }
    
    # 파서 생성
    parser = StrategyParser(strategy_definition, bars)
    strategy_func = parser.create_strategy_function()
    
    # 테스트
    for i, bar in enumerate(bars):
        result = strategy_func(bar)
        print(f"Bar {i}: O={bar.open} H={bar.high} L={bar.low} C={bar.close} V={bar.volume}")
        print(f"  → Result: {result}")
        assert result is not None, f"Bar {i}는 모든 조건을 만족해야 합니다"
    
    print("PASS: All OHLCV fields test")


if __name__ == "__main__":
    print("=" * 60)
    print("OHLCV Condition Tests")
    print("=" * 60)
    
    print("\n[Test 1] Close > EMA condition")
    print("-" * 60)
    test_ohlcv_condition_close_greater_than_ema()
    
    print("\n[Test 2] Volume > average Volume condition")
    print("-" * 60)
    test_ohlcv_condition_volume_greater_than_average()
    
    print("\n[Test 3] Combined condition (Close > EMA AND Volume > average)")
    print("-" * 60)
    test_ohlcv_condition_combined()
    
    print("\n[Test 4] Close cross_above EMA condition")
    print("-" * 60)
    test_ohlcv_condition_cross_above()
    
    print("\n[Test 5] All OHLCV fields test")
    print("-" * 60)
    test_ohlcv_all_fields()
    
    print("\n" + "=" * 60)
    print("ALL OHLCV TESTS PASSED!")
    print("=" * 60)

