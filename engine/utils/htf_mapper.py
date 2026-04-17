"""
멀티 타임프레임(MTF) 인덱스 매퍼

베이스 TF의 각 봉에서, 상위 TF(HTF)의 "이미 완전히 닫힌 마지막 봉 인덱스"를
사전에 계산해 배열로 제공한다. 런타임에 look-ahead가 구조적으로 불가능하게 보장.

닫힘 조건 (핵심):
    htf_bar.open_time + htf_duration <= base_bar.open_time

예: base 5m 10:05 → 1h HTF는 9:00+3600=10:00 ≤ 10:05이므로 9:00 봉은 닫힘.
    10:00 HTF 봉은 10:00+3600=11:00 > 10:05 → 아직 열린 상태, 노출 금지.

결정성:
  - 입력(bars, tf_interval)이 같으면 출력(매핑 배열)이 동일
  - 난수/시스템시간 사용 없음
"""

from __future__ import annotations

from typing import List

from engine.models.bar import Bar


# 지원 타임프레임의 초 단위 길이 (바이낸스 표준과 일치)
INTERVAL_SECONDS = {
    "1m": 60,
    "3m": 3 * 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "30m": 30 * 60,
    "1h": 60 * 60,
    "2h": 2 * 60 * 60,
    "4h": 4 * 60 * 60,
    "6h": 6 * 60 * 60,
    "8h": 8 * 60 * 60,
    "12h": 12 * 60 * 60,
    "1d": 24 * 60 * 60,
    "3d": 3 * 24 * 60 * 60,
    "1w": 7 * 24 * 60 * 60,
}


def interval_to_seconds(tf: str) -> int:
    """'1h' → 3600. 미지원 TF는 ValueError."""
    if tf not in INTERVAL_SECONDS:
        raise ValueError(f"지원하지 않는 타임프레임: {tf}")
    return INTERVAL_SECONDS[tf]


def build_htf_index_map(
    base_bars: List[Bar],
    htf_bars: List[Bar],
    htf_interval_sec: int,
) -> List[int]:
    """base bar별로 "이미 닫힌 HTF 봉의 인덱스"를 반환하는 배열 생성.

    규칙:
      - htf_bars[j].timestamp + htf_interval_sec <= base_bars[i].timestamp
        을 만족하는 최대 j 가 base_bars[i]의 매핑 값
      - 아직 어떤 HTF 봉도 닫히지 않았으면 -1 (값 조회 시 None 처리)
      - base/htf 모두 timestamp 오름차순 전제

    복잡도: O(N + M) 투포인터

    Args:
        base_bars: 베이스 타임프레임 봉 (정렬됨)
        htf_bars: 상위 타임프레임 봉 (정렬됨)
        htf_interval_sec: HTF 봉의 길이(초). interval_to_seconds("1h") 등으로 구함.

    Returns:
        길이 == len(base_bars) 인 정수 배열. 각 원소는 해당 base bar 시점에
        "이미 완전히 닫힌" htf_bars의 최대 인덱스(없으면 -1).
    """
    if htf_interval_sec <= 0:
        raise ValueError(f"htf_interval_sec은 양수여야 합니다: {htf_interval_sec}")

    n = len(base_bars)
    m = len(htf_bars)
    mapping: List[int] = [-1] * n

    if n == 0 or m == 0:
        return mapping

    j = -1  # 마지막으로 확정(닫힘)된 HTF 인덱스
    for i, b in enumerate(base_bars):
        base_ts = b.timestamp
        # j+1부터 전진하며, 닫힘 조건을 만족하는 동안 j를 밀어올림
        while j + 1 < m and htf_bars[j + 1].timestamp + htf_interval_sec <= base_ts:
            j += 1
        mapping[i] = j

    return mapping


def resolve_htf_index(mapping: List[int], base_index: int) -> int:
    """매핑 배열에서 base_index에 해당하는 HTF 인덱스를 안전하게 조회.

    Returns:
        HTF 인덱스. "아직 닫힌 HTF 봉 없음"인 경우 -1.
    """
    if base_index < 0 or base_index >= len(mapping):
        raise IndexError(f"base_index {base_index} 범위 초과 (len={len(mapping)})")
    return mapping[base_index]
