"""
바이낸스 아카이브 + REST 결과를 병합해 AlgoForge CSV 포맷으로 저장.

AlgoForge CSV 포맷 (기존과 동일):
  dt,do,dh,dl,dc,dv,dd
  2024-05-31 00:00:00,0.5231,0.5250,0.5215,0.5242,1234567.8,1

- dt: UTC 기준 'YYYY-MM-DD HH:MM:SS'
- dd: 봉 방향 (close > open → 1, close < open → -1, else 0)
"""

from __future__ import annotations

import csv
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from engine.data.binance.klines_archive import (
    RawKline,
    VALID_INTERVALS,
    download_archive_range,
)
from engine.data.binance.klines_rest import INTERVAL_TO_MS, fetch_rest_range

logger = logging.getLogger(__name__)


def _compute_direction(o: float, c: float) -> int:
    if c > o:
        return 1
    if c < o:
        return -1
    return 0


def _kline_to_csv_row(k: RawKline) -> list:
    dt = datetime.fromtimestamp(k.open_time_sec, tz=timezone.utc)
    return [
        dt.strftime("%Y-%m-%d %H:%M:%S"),
        f"{k.open}",
        f"{k.high}",
        f"{k.low}",
        f"{k.close}",
        f"{k.volume}",
        _compute_direction(k.open, k.close),
    ]


def _dedupe_sorted(klines: List[RawKline]) -> List[RawKline]:
    klines.sort(key=lambda k: k.open_time_ms)
    out: List[RawKline] = []
    last = -1
    for k in klines:
        if k.open_time_ms == last:
            continue
        out.append(k)
        last = k.open_time_ms
    return out


def fetch_and_merge(
    symbol: str,
    market_type: str,
    interval: str,
    start_date: date,
    end_date: date,
    cache_dir: Path,
) -> List[RawKline]:
    """아카이브 + REST를 병합한 kline 리스트 반환 (CSV는 쓰지 않음).

    로직:
      1) 아카이브에서 [start_date, end_date] 전체 구간 시도
      2) 아카이브 결과의 마지막 봉 이후 ~ end_date 23:59:59 구간은 REST로 보완
      3) 아카이브가 전부 404이면 전체를 REST로 수집
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"지원하지 않는 interval: {interval}")

    archive_klines = download_archive_range(
        symbol=symbol,
        market_type=market_type,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        cache_dir=cache_dir,
    )

    # 요청 구간 경계 (UTC 밀리초)
    start_ms = int(datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)
    end_dt = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1) - timedelta(milliseconds=1)
    end_ms = int(end_dt.timestamp() * 1000)

    step_ms = INTERVAL_TO_MS[interval]

    # REST 보완 시작 지점: 아카이브가 커버한 마지막 봉 open_time + step, 없으면 start_ms
    if archive_klines:
        rest_start_ms = archive_klines[-1].open_time_ms + step_ms
    else:
        rest_start_ms = start_ms

    rest_klines: List[RawKline] = []
    if rest_start_ms <= end_ms:
        rest_klines = fetch_rest_range(
            symbol=symbol,
            market_type=market_type,
            interval=interval,
            start_ms=rest_start_ms,
            end_ms=end_ms,
        )

    merged = archive_klines + rest_klines
    merged = _dedupe_sorted(merged)

    # 경계 필터: 혹시 아카이브가 요청 범위 밖 봉을 포함했다면 제거
    merged = [k for k in merged if start_ms <= k.open_time_ms <= end_ms]

    logger.info(
        f"병합 완료: 아카이브 {len(archive_klines)} + REST {len(rest_klines)} "
        f"→ 최종 {len(merged)} klines"
    )
    return merged


def write_algoforge_csv(klines: List[RawKline], out_path: Path) -> None:
    """AlgoForge CSV 포맷으로 저장 (기존 load_bars_from_csv와 호환)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["dt", "do", "dh", "dl", "dc", "dv", "dd"])
        for k in klines:
            writer.writerow(_kline_to_csv_row(k))
    logger.info(f"CSV 저장: {out_path} ({len(klines)} rows)")


def fetch_binance_to_csv(
    symbol: str,
    market_type: str,
    interval: str,
    start_date: date,
    end_date: date,
    out_path: Path,
    cache_dir: Path,
) -> int:
    """편의 함수: 다운로드 → 병합 → CSV 저장. 총 행 수 반환."""
    klines = fetch_and_merge(
        symbol=symbol,
        market_type=market_type,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        cache_dir=cache_dir,
    )
    write_algoforge_csv(klines, out_path)
    return len(klines)
