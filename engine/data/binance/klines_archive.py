"""
바이낸스 공개 아카이브(data.binance.vision) 기반 klines 다운로더

- 월 단위 ZIP을 우선 다운로드 (대량 백필에 효율적)
- 월 ZIP이 없는 최근 구간은 일 단위 ZIP으로 보완
- 각 ZIP은 SHA256 체크섬 파일로 검증 가능

결정성:
- 동일 (symbol, market_type, timeframe, 날짜) → 동일 파일 (바이낸스가 immutable 보장)
- 로컬 캐시 디렉토리에 저장하여 재실행 시 네트워크 호출 없음
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

import httpx

logger = logging.getLogger(__name__)

ARCHIVE_BASE = "https://data.binance.vision/data"


# data.binance.vision이 공식 지원하는 klines 인터벌
VALID_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1mo",
}


@dataclass(frozen=True)
class RawKline:
    """아카이브 CSV 한 행을 그대로 담는 경량 구조체.

    바이낸스 klines CSV 컬럼 순서 (공식 문서 기준):
    open_time, open, high, low, close, volume,
    close_time, quote_asset_volume, number_of_trades,
    taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore
    """
    open_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time_ms: int

    @property
    def open_time_sec(self) -> int:
        return self.open_time_ms // 1000


def _market_path(market_type: str) -> str:
    """market_type을 아카이브 경로 세그먼트로 변환."""
    if market_type == "spot":
        return "spot"
    if market_type == "futures_um":
        return "futures/um"
    raise ValueError(f"지원하지 않는 market_type: {market_type}")


def _monthly_url(market_type: str, symbol: str, interval: str, year: int, month: int) -> str:
    mpath = _market_path(market_type)
    return (
        f"{ARCHIVE_BASE}/{mpath}/monthly/klines/{symbol}/{interval}/"
        f"{symbol}-{interval}-{year:04d}-{month:02d}.zip"
    )


def _daily_url(market_type: str, symbol: str, interval: str, d: date) -> str:
    mpath = _market_path(market_type)
    return (
        f"{ARCHIVE_BASE}/{mpath}/daily/klines/{symbol}/{interval}/"
        f"{symbol}-{interval}-{d.isoformat()}.zip"
    )


def _checksum_url(zip_url: str) -> str:
    return zip_url + ".CHECKSUM"


def _iter_months(start: date, end: date) -> Iterable[tuple[int, int]]:
    """start <= (year, month) <= end 구간의 월 튜플을 생성."""
    y, m = start.year, start.month
    end_y, end_m = end.year, end.month
    while (y, m) <= (end_y, end_m):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def _iter_days(start: date, end: date) -> Iterable[date]:
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _download_with_verify(
    client: httpx.Client,
    zip_url: str,
    cache_path: Path,
) -> Optional[bytes]:
    """ZIP을 다운로드하고 .CHECKSUM 파일로 SHA256 검증.

    파일이 존재하지 않으면 None 반환 (404 정상 케이스).
    캐시 히트 시 네트워크 호출 생략.
    """
    if cache_path.exists():
        return cache_path.read_bytes()

    resp = client.get(zip_url)
    if resp.status_code == 404:
        logger.debug(f"아카이브 없음 (404): {zip_url}")
        return None
    resp.raise_for_status()
    zip_bytes = resp.content

    # 체크섬 검증 (바이낸스는 모든 아카이브에 .CHECKSUM 제공)
    checksum_resp = client.get(_checksum_url(zip_url))
    if checksum_resp.status_code == 200:
        expected = checksum_resp.text.strip().split()[0].lower()
        actual = hashlib.sha256(zip_bytes).hexdigest().lower()
        if expected != actual:
            raise RuntimeError(
                f"체크섬 불일치: {zip_url}\n expected={expected} actual={actual}"
            )

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(zip_bytes)
    return zip_bytes


def _parse_zip_to_klines(zip_bytes: bytes) -> List[RawKline]:
    """ZIP 내부 단일 CSV를 파싱해 RawKline 리스트 반환."""
    klines: List[RawKline] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        if len(names) != 1:
            raise RuntimeError(f"예상치 못한 ZIP 구조: {names}")
        with zf.open(names[0]) as f:
            text = io.TextIOWrapper(f, encoding="utf-8", newline="")
            reader = csv.reader(text)
            first = next(reader, None)
            if first is None:
                return klines
            # 바이낸스는 최근 일부 아카이브에 헤더를 포함하기도 함
            if first and not first[0].isdigit():
                pass  # 헤더라고 판단 → 스킵
            else:
                klines.append(_row_to_kline(first))
            for row in reader:
                if not row:
                    continue
                klines.append(_row_to_kline(row))
    return klines


def _row_to_kline(row: List[str]) -> RawKline:
    return RawKline(
        open_time_ms=int(row[0]),
        open=float(row[1]),
        high=float(row[2]),
        low=float(row[3]),
        close=float(row[4]),
        volume=float(row[5]),
        close_time_ms=int(row[6]),
    )


def download_archive_range(
    symbol: str,
    market_type: str,
    interval: str,
    start_date: date,
    end_date: date,
    cache_dir: Path,
    timeout_sec: float = 60.0,
) -> List[RawKline]:
    """지정 구간의 klines를 아카이브에서 다운로드·병합.

    전략:
      1) 월이 완전히 [start_date, end_date] 안에 들어가면 monthly ZIP 사용
      2) 경계 월(부분 월)은 daily ZIP으로 보완
      3) 바이낸스가 월 아카이브를 올리지 않은 최근 월은 daily ZIP으로 대체
    404는 정상 케이스로 무시 (호출 측에서 REST로 보완 예정).

    Args:
        symbol: "XRPUSDT" 등 (대문자)
        market_type: "spot" | "futures_um"
        interval: "5m" 등 (VALID_INTERVALS)
        start_date/end_date: 포함, UTC 날짜
        cache_dir: 다운로드 캐시 디렉토리 (재사용)
        timeout_sec: HTTP 타임아웃

    Returns:
        open_time 오름차순으로 정렬된 RawKline 리스트 (중복 제거됨)
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"지원하지 않는 interval: {interval}")
    if start_date > end_date:
        raise ValueError(f"start_date > end_date: {start_date} > {end_date}")

    cache_root = cache_dir / _market_path(market_type).replace("/", "_") / symbol / interval

    all_klines: List[RawKline] = []
    covered_days: set[date] = set()

    with httpx.Client(timeout=timeout_sec, follow_redirects=True) as client:
        # 1) 완전히 포함된 월은 monthly ZIP
        for y, m in _iter_months(start_date, end_date):
            month_first = date(y, m, 1)
            if m == 12:
                month_last = date(y, 12, 31)
            else:
                month_last = date(y, m + 1, 1) - timedelta(days=1)

            # 월 전체가 요청 범위에 포함되어야 monthly 사용
            if month_first < start_date or month_last > end_date:
                continue

            url = _monthly_url(market_type, symbol, interval, y, m)
            cache_path = cache_root / f"monthly_{y:04d}-{m:02d}.zip"
            zip_bytes = _download_with_verify(client, url, cache_path)
            if zip_bytes is None:
                logger.info(f"월 아카이브 없음 → 일 단위로 보완 예정: {y}-{m:02d}")
                continue

            klines = _parse_zip_to_klines(zip_bytes)
            all_klines.extend(klines)
            d = month_first
            while d <= month_last:
                covered_days.add(d)
                d += timedelta(days=1)
            logger.info(f"월 아카이브 로드: {y}-{m:02d} ({len(klines)} klines)")

        # 2) 아직 커버되지 않은 날짜는 daily ZIP
        for d in _iter_days(start_date, end_date):
            if d in covered_days:
                continue
            url = _daily_url(market_type, symbol, interval, d)
            cache_path = cache_root / f"daily_{d.isoformat()}.zip"
            zip_bytes = _download_with_verify(client, url, cache_path)
            if zip_bytes is None:
                # 아직 아카이브가 없는 최근 날 → REST가 보완
                continue
            klines = _parse_zip_to_klines(zip_bytes)
            all_klines.extend(klines)
            logger.debug(f"일 아카이브 로드: {d} ({len(klines)} klines)")

    # 정렬 + 중복 제거 (open_time 기준)
    all_klines.sort(key=lambda k: k.open_time_ms)
    deduped: List[RawKline] = []
    last_ts = -1
    for k in all_klines:
        if k.open_time_ms == last_ts:
            continue
        deduped.append(k)
        last_ts = k.open_time_ms

    logger.info(
        f"아카이브 총 {len(deduped)} klines 로드 "
        f"({symbol} {market_type} {interval} {start_date}~{end_date})"
    )
    return deduped
