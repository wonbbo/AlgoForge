"""
바이낸스 REST API 기반 klines 수집 (아카이브 미커버 최근 구간 보완용)

Endpoints:
- Spot:     GET https://api.binance.com/api/v3/klines
- Futures:  GET https://fapi.binance.com/fapi/v1/klines

특징:
- 1회 요청당 최대 1000봉
- 시간 범위 페이지네이션 (startTime 증가)
- 레이트리밋: spot IP weight 6000/min, futures IP weight 2400/min — 여유롭게 sleep으로 완화
- 완결되지 않은 현재 봉은 제외 (결정성)
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

import httpx

from engine.data.binance.klines_archive import RawKline, VALID_INTERVALS

logger = logging.getLogger(__name__)

SPOT_BASE = "https://api.binance.com"
FUTURES_UM_BASE = "https://fapi.binance.com"

# 바이낸스가 허용하는 interval (REST)
INTERVAL_TO_MS = {
    "1m": 60_000,
    "3m": 3 * 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "2h": 2 * 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "6h": 6 * 60 * 60_000,
    "8h": 8 * 60 * 60_000,
    "12h": 12 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
    "3d": 3 * 24 * 60 * 60_000,
    "1w": 7 * 24 * 60 * 60_000,
}

MAX_LIMIT = 1000  # 바이낸스 klines 요청당 최대


def _endpoint(market_type: str) -> str:
    if market_type == "spot":
        return f"{SPOT_BASE}/api/v3/klines"
    if market_type == "futures_um":
        return f"{FUTURES_UM_BASE}/fapi/v1/klines"
    raise ValueError(f"지원하지 않는 market_type: {market_type}")


def _row_to_kline(row: list) -> RawKline:
    """바이낸스 REST 응답 한 행을 RawKline으로 변환.

    응답 형식 (list of list):
      [open_time, open, high, low, close, volume,
       close_time, quote_asset_vol, num_trades,
       taker_buy_base_vol, taker_buy_quote_vol, ignore]
    """
    return RawKline(
        open_time_ms=int(row[0]),
        open=float(row[1]),
        high=float(row[2]),
        low=float(row[3]),
        close=float(row[4]),
        volume=float(row[5]),
        close_time_ms=int(row[6]),
    )


def fetch_rest_range(
    symbol: str,
    market_type: str,
    interval: str,
    start_ms: int,
    end_ms: int,
    timeout_sec: float = 30.0,
    sleep_between_requests: float = 0.25,
    exclude_unclosed: bool = True,
) -> List[RawKline]:
    """[start_ms, end_ms] 구간의 klines를 REST로 수집.

    Args:
        symbol: "XRPUSDT" 등
        market_type: "spot" | "futures_um"
        interval: "5m" 등
        start_ms: 구간 시작 (포함, 밀리초 UNIX)
        end_ms: 구간 끝 (포함, 밀리초 UNIX)
        exclude_unclosed: 현재 시각 기준 아직 마감되지 않은 봉 제외 (결정성)

    Returns:
        open_time 오름차순으로 정렬된 RawKline 리스트 (중복 제거됨)
    """
    if interval not in INTERVAL_TO_MS:
        raise ValueError(f"REST에서 지원하지 않는 interval: {interval}")
    if start_ms > end_ms:
        return []

    url = _endpoint(market_type)
    step_ms = INTERVAL_TO_MS[interval]

    # 마감되지 않은 봉 제외: now 기준 마지막 '닫힌' 봉의 open_time 계산
    if exclude_unclosed:
        now_ms = int(time.time() * 1000)
        last_closed_open_ms = ((now_ms // step_ms) * step_ms) - step_ms
        end_ms = min(end_ms, last_closed_open_ms)
        if end_ms < start_ms:
            return []

    all_klines: List[RawKline] = []
    cursor = start_ms

    with httpx.Client(timeout=timeout_sec) as client:
        while cursor <= end_ms:
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": cursor,
                "endTime": end_ms,
                "limit": MAX_LIMIT,
            }
            resp = client.get(url, params=params)
            resp.raise_for_status()
            rows = resp.json()
            if not rows:
                break

            batch = [_row_to_kline(r) for r in rows]
            all_klines.extend(batch)

            last_open_ms = batch[-1].open_time_ms
            # 다음 커서: 마지막 봉 다음 봉부터
            next_cursor = last_open_ms + step_ms
            if next_cursor <= cursor:
                # 무한루프 방지 (이론상 발생하지 않음)
                break
            cursor = next_cursor

            if len(batch) < MAX_LIMIT:
                # 더 이상 받을 게 없으면 종료
                break

            time.sleep(sleep_between_requests)

    # 정렬 + 중복 제거
    all_klines.sort(key=lambda k: k.open_time_ms)
    deduped: List[RawKline] = []
    last_ts = -1
    for k in all_klines:
        if k.open_time_ms == last_ts:
            continue
        deduped.append(k)
        last_ts = k.open_time_ms

    logger.info(
        f"REST 수집 {len(deduped)} klines "
        f"({symbol} {market_type} {interval} "
        f"{start_ms}~{end_ms} ms)"
    )
    return deduped
