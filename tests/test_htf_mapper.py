"""
HTF 인덱스 매퍼 단위 테스트

핵심 검증 포인트:
  1) Look-ahead 차단: 아직 닫히지 않은 HTF 봉은 절대 노출되지 않음
  2) 결정성: 동일 입력 → 동일 출력
  3) 경계 처리: HTF가 base보다 먼저/나중 시작하는 경우
  4) 다양한 TF 조합 (5m/1h, 5m/1d, 1m/4h 등)
"""

from __future__ import annotations

from typing import List

import pytest

from engine.models.bar import Bar
from engine.utils.htf_mapper import (
    INTERVAL_SECONDS,
    build_htf_index_map,
    interval_to_seconds,
    resolve_htf_index,
)


def _mk_bars(timestamps: List[int], price: float = 1.0) -> List[Bar]:
    """timestamp 리스트로부터 간단한 Bar 리스트 생성 (OHLC = price)."""
    return [
        Bar(timestamp=ts, open=price, high=price, low=price, close=price,
            volume=1.0, direction=0)
        for ts in timestamps
    ]


# ---------------------------------------------------------------------------
# interval_to_seconds
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_interval_to_seconds_standard():
    assert interval_to_seconds("1m") == 60
    assert interval_to_seconds("5m") == 300
    assert interval_to_seconds("1h") == 3600
    assert interval_to_seconds("4h") == 4 * 3600
    assert interval_to_seconds("1d") == 86400


@pytest.mark.unit
def test_interval_to_seconds_invalid():
    with pytest.raises(ValueError):
        interval_to_seconds("13h")


# ---------------------------------------------------------------------------
# build_htf_index_map — 기본 동작
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_empty_inputs():
    assert build_htf_index_map([], [], 3600) == []
    base = _mk_bars([0, 300, 600])
    assert build_htf_index_map(base, [], 3600) == [-1, -1, -1]
    htf = _mk_bars([0, 3600])
    assert build_htf_index_map([], htf, 3600) == []


@pytest.mark.unit
def test_5m_base_with_1h_htf_basic():
    """5분봉 12개(1시간) + 1시간봉 2개. 첫 1h 봉이 닫히는 시점 이후로만 매핑."""
    # base: 10:00, 10:05, 10:10 ... 10:55 (12개) + 11:00, 11:05 (2개)
    base_ts = [10 * 3600 + i * 300 for i in range(14)]
    base = _mk_bars(base_ts)
    # HTF: 10:00, 11:00 (2개, 1h봉)
    htf = _mk_bars([10 * 3600, 11 * 3600])

    mapping = build_htf_index_map(base, htf, htf_interval_sec=3600)

    # base[0] = 10:00. HTF[0] open_time+3600 = 11:00 > 10:00 → 닫힘 없음 → -1
    # base[11] = 10:55. 11:00 > 10:55 → 여전히 -1
    # base[12] = 11:00. HTF[0].open_time+3600 = 11:00 <= 11:00 → j=0 닫힘
    # base[13] = 11:05. HTF[1] open+3600 = 12:00 > 11:05 → j=0 유지
    expected = [-1] * 12 + [0, 0]
    assert mapping == expected


@pytest.mark.unit
def test_look_ahead_blocked_strict_inequality():
    """'현재 HTF 봉'은 노출되지 않아야 함. base가 HTF open과 동일 시점이어도 금지."""
    # HTF 1h 봉 두 개: 10:00, 11:00
    htf = _mk_bars([10 * 3600, 11 * 3600])
    # base 시점: 10:00, 10:30, 10:59, 11:00, 11:01
    base = _mk_bars([10 * 3600, 10 * 3600 + 1800, 10 * 3600 + 3540,
                     11 * 3600, 11 * 3600 + 60])
    mapping = build_htf_index_map(base, htf, 3600)

    # 10:00, 10:30, 10:59 → HTF[0] (10:00 open)는 11:00에 닫힘 → 아직 안 닫힘 → -1
    # 11:00 → HTF[0] 가 지금 "막 닫힘" → j=0 사용 가능 (<=로 허용)
    # 11:01 → HTF[0] 여전히 사용 가능, HTF[1]은 12:00에 닫히므로 아직 -1
    assert mapping == [-1, -1, -1, 0, 0]


@pytest.mark.unit
def test_htf_starts_before_base():
    """HTF가 base 시작 이전부터 존재하는 경우 (과거 히스토리 보유)."""
    # HTF 1h: 8:00, 9:00, 10:00
    htf = _mk_bars([8 * 3600, 9 * 3600, 10 * 3600])
    # base 5m: 9:30, 9:55, 10:00, 10:05
    base = _mk_bars([9 * 3600 + 1800, 9 * 3600 + 3300,
                     10 * 3600, 10 * 3600 + 300])
    mapping = build_htf_index_map(base, htf, 3600)
    # 9:30 → HTF[0] closes at 9:00 (8:00+3600) ≤ 9:30 ✓ → j=0
    #        HTF[1] closes at 10:00 > 9:30 → 중단
    # 9:55 → 여전히 j=0
    # 10:00 → HTF[1] closes at 10:00 ≤ 10:00 ✓ → j=1
    # 10:05 → HTF[2] closes at 11:00 > 10:05 → j=1 유지
    assert mapping == [0, 0, 1, 1]


@pytest.mark.unit
def test_htf_daily_with_5m_base():
    """5m base + 1d HTF. 자정(UTC 00:00)에 HTF 봉이 닫힘."""
    day_sec = 86400
    # HTF 1d: day 0, day 1 (UTC 자정 기준)
    htf = _mk_bars([0, day_sec])
    # base 5m 세 개: day 0 11:55, day 1 00:00, day 1 00:05
    base = _mk_bars([
        11 * 3600 + 55 * 60,
        day_sec,
        day_sec + 300,
    ])
    mapping = build_htf_index_map(base, htf, day_sec)
    # day 0 11:55 → HTF[0] closes at day 1 00:00 > 11:55 → -1
    # day 1 00:00 → HTF[0] closes at day 1 00:00 ≤ day 1 00:00 → j=0
    # day 1 00:05 → HTF[1] closes at day 2 > day 1 00:05 → j=0 유지
    assert mapping == [-1, 0, 0]


@pytest.mark.unit
def test_htf_4h_with_1m_base_sequence():
    """1m base 그룹을 4h HTF와 매핑. 다수 경계 검증."""
    hour = 3600
    # HTF 4h: 0, 4h, 8h, 12h
    htf = _mk_bars([0, 4 * hour, 8 * hour, 12 * hour])
    # base 1m: 3:59, 4:00, 7:59, 8:00, 8:01
    base = _mk_bars([3 * hour + 59 * 60, 4 * hour,
                     7 * hour + 59 * 60, 8 * hour, 8 * hour + 60])
    mapping = build_htf_index_map(base, htf, 4 * hour)
    # 3:59 → HTF[0] closes at 4:00 > 3:59 → -1
    # 4:00 → HTF[0] closes at 4:00 ≤ 4:00 → j=0
    # 7:59 → HTF[1] closes at 8:00 > 7:59 → j=0
    # 8:00 → HTF[1] closes at 8:00 ≤ 8:00 → j=1
    # 8:01 → j=1 유지
    assert mapping == [-1, 0, 0, 1, 1]


# ---------------------------------------------------------------------------
# 결정성 & 멱등성
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_deterministic_same_inputs_same_output():
    base = _mk_bars([i * 300 for i in range(100)])
    htf = _mk_bars([i * 3600 for i in range(10)])
    a = build_htf_index_map(base, htf, 3600)
    b = build_htf_index_map(base, htf, 3600)
    assert a == b


@pytest.mark.unit
def test_mapping_monotonic_non_decreasing():
    """매핑은 반드시 비감소(non-decreasing)여야 함 (시간 단조성)."""
    base = _mk_bars([i * 60 for i in range(200)])  # 1m, 200봉
    htf = _mk_bars([i * 3600 for i in range(4)])   # 1h, 4봉
    mapping = build_htf_index_map(base, htf, 3600)
    for i in range(1, len(mapping)):
        assert mapping[i] >= mapping[i - 1], \
            f"monotonic violation at i={i}: {mapping[i-1]} -> {mapping[i]}"


# ---------------------------------------------------------------------------
# resolve_htf_index
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_resolve_htf_index_basic():
    mapping = [-1, -1, 0, 0, 1]
    assert resolve_htf_index(mapping, 0) == -1
    assert resolve_htf_index(mapping, 2) == 0
    assert resolve_htf_index(mapping, 4) == 1


@pytest.mark.unit
def test_resolve_htf_index_out_of_range():
    mapping = [0, 1]
    with pytest.raises(IndexError):
        resolve_htf_index(mapping, 5)
    with pytest.raises(IndexError):
        resolve_htf_index(mapping, -1)


# ---------------------------------------------------------------------------
# 비정상 입력
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_zero_or_negative_interval_rejected():
    base = _mk_bars([0, 300])
    htf = _mk_bars([0])
    with pytest.raises(ValueError):
        build_htf_index_map(base, htf, 0)
    with pytest.raises(ValueError):
        build_htf_index_map(base, htf, -60)
