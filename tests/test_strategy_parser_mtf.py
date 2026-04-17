"""
StrategyParser 멀티 타임프레임(MTF) E2E 테스트

검증 포인트:
  1) @tf 접미사 파싱 → HTF 인디케이터 참조
  2) HTF 봉이 닫히기 전 구간에서 조건이 발동하지 않음 (look-ahead 차단)
  3) HTF 봉이 닫힌 이후 구간에서 조건이 정상 평가됨
  4) @tf 없는 기존 전략이 그대로 동작 (backward compat)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.models.bar import Bar
from engine.utils.strategy_parser import StrategyParser


def _bars(timestamps, closes):
    return [
        Bar(timestamp=ts, open=c, high=c + 1, low=c - 1, close=c,
            volume=100.0, direction=0)
        for ts, c in zip(timestamps, closes)
    ]


@pytest.mark.unit
def test_mtf_parser_looks_up_htf_indicator_only_after_htf_close():
    """base=5m, HTF=1h. HTF EMA 참조는 첫 HTF 봉(10:00)이 닫힌 11:00 이후에만 평가돼야 함."""
    hour = 3600
    # base 5m: 10:00 ~ 11:55 (24봉)
    base_ts = [10 * hour + i * 300 for i in range(24)]
    base_closes = [100.0 + i * 0.1 for i in range(24)]
    base = _bars(base_ts, base_closes)

    # HTF 1h: 10:00, 11:00, 12:00 (봉 3개, close 증가)
    htf = _bars([10 * hour, 11 * hour, 12 * hour], [100.0, 105.0, 110.0])

    strategy_definition = {
        "indicators": [
            {
                "id": "ema_1h",
                "type": "ema",
                "timeframe": "1h",
                "params": {"source": "close", "period": 2},
            }
        ],
        "entry": {
            "long": {
                "and": [
                    {"left": {"price": "close"}, "op": ">",
                     "right": {"ref": "ema_1h@1h"}}
                ]
            },
            "short": {"and": []},
        },
        "stop_loss": {"type": "fixed_percent", "percent": 2.0},
    }

    parser = StrategyParser(strategy_definition, base, htf_data={"1h": (htf, None)})
    strategy_func = parser.create_strategy_function()

    # 10:00 ~ 10:55 구간 (base 0~11): HTF[0]=10:00 봉은 아직 안 닫힘 → None
    for i in range(12):
        assert strategy_func(base[i]) is None, f"look-ahead: i={i} should be None"

    # 11:00 base[12] 이후: HTF[0] 닫혔으니 ema_1h 값 조회 가능 → 조건 평가됨
    # base close가 100보다 크니 "close > ema_1h(100)" true 예상
    fired_after = [strategy_func(base[i]) is not None for i in range(12, 24)]
    assert any(fired_after), "HTF가 닫힌 후에는 신호가 발생해야 함"


@pytest.mark.unit
def test_mtf_htf_index_mapping_monotonic_across_calls():
    """MTF 파서에서 HTF 매핑이 단조 비감소여야 함 (StrategyParser 내부 일관성)."""
    hour = 3600
    base = _bars([10 * hour + i * 300 for i in range(50)],
                 [100.0 + i * 0.1 for i in range(50)])
    htf = _bars([10 * hour + i * hour for i in range(5)],
                [100.0, 101.0, 102.0, 103.0, 104.0])

    parser = StrategyParser(
        strategy_definition={"indicators": [], "entry": {"long": {"and": []}, "short": {"and": []}},
                             "stop_loss": {"type": "fixed_percent", "percent": 2.0}},
        bars=base,
        htf_data={"1h": (htf, None)},
    )
    mapping = parser.htf_index_maps["1h"]
    assert len(mapping) == len(base)
    for i in range(1, len(mapping)):
        assert mapping[i] >= mapping[i - 1]


@pytest.mark.unit
def test_mtf_no_htf_data_falls_back_to_single_tf():
    """htf_data 없이 생성하면 기존 단일-TF 동작과 동일해야 함 (backward compat)."""
    bars = [
        Bar(timestamp=1000 + i * 5, open=100 + i, high=101 + i,
            low=99 + i, close=100 + i, volume=1000.0, direction=1)
        for i in range(10)
    ]
    strategy_definition = {
        "indicators": [
            {"id": "ema_3", "type": "ema",
             "params": {"source": "close", "period": 3}}
        ],
        "entry": {
            "long": {"and": [
                {"left": {"price": "close"}, "op": ">",
                 "right": {"ref": "ema_3"}}  # @tf 없음 → base
            ]},
            "short": {"and": []},
        },
        "stop_loss": {"type": "fixed_percent", "percent": 2.0},
    }
    parser = StrategyParser(strategy_definition, bars)
    assert "base" in parser.indicator_calcs
    assert parser.htf_index_maps == {}
    # 몇 번째 이후 봉에서 조건이 true가 되어야 함
    fn = parser.create_strategy_function()
    results = [fn(b) for b in bars]
    # 뒤쪽 봉 몇 개는 non-None 이어야 함
    assert any(r is not None for r in results[3:])


@pytest.mark.unit
def test_mtf_parse_indicator_ref_separates_tf():
    """_parse_indicator_ref가 'x@1h' → ('x', '1h'), 'x' → ('x', 'base') 로 분리."""
    bars = [Bar(timestamp=1000 + i, open=1, high=1, low=1, close=1,
                volume=1, direction=0) for i in range(3)]
    parser = StrategyParser(
        strategy_definition={"indicators": [],
                             "entry": {"long": {"and": []}, "short": {"and": []}},
                             "stop_loss": {"type": "fixed_percent", "percent": 2.0}},
        bars=bars,
    )
    assert parser._parse_indicator_ref("ema_3") == ("ema_3", "base")
    assert parser._parse_indicator_ref("ema_3@1h") == ("ema_3", "1h")
    # dot 경로 보존
    assert parser._parse_indicator_ref("macd.signal@4h") == ("macd_signal", "4h")


@pytest.mark.unit
def test_mtf_rejects_base_in_htf_data():
    bars = [Bar(timestamp=1000, open=1, high=1, low=1, close=1, volume=1, direction=0)]
    with pytest.raises(ValueError):
        StrategyParser(
            strategy_definition={"indicators": [],
                                 "entry": {"long": {"and": []}, "short": {"and": []}},
                                 "stop_loss": {"type": "fixed_percent", "percent": 2.0}},
            bars=bars,
            htf_data={"base": (bars, None)},
        )
