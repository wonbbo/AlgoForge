"""
바이낸스 fetcher 단위 테스트 (네트워크 호출 없음)

- 아카이브 ZIP 파싱 로직
- URL 조립 로직
- 중복 제거/정렬
- CSV 포맷 변환
- merger의 로컬 동작

네트워크 통합 테스트는 @pytest.mark.integration으로 별도 분리.
"""

import csv
import io
import zipfile
from datetime import date
from pathlib import Path

import pytest

from engine.data.binance.klines_archive import (
    RawKline,
    VALID_INTERVALS,
    _daily_url,
    _iter_days,
    _iter_months,
    _market_path,
    _monthly_url,
    _parse_zip_to_klines,
)
from engine.data.binance.klines_rest import INTERVAL_TO_MS, _endpoint
from engine.data.binance.merger import (
    _compute_direction,
    _dedupe_sorted,
    _kline_to_csv_row,
    write_algoforge_csv,
)


# -----------------------------------------------------------------------
# URL/경로 조립
# -----------------------------------------------------------------------


@pytest.mark.unit
def test_market_path_spot_and_futures():
    assert _market_path("spot") == "spot"
    assert _market_path("futures_um") == "futures/um"


@pytest.mark.unit
def test_market_path_invalid():
    with pytest.raises(ValueError):
        _market_path("unknown")


@pytest.mark.unit
def test_monthly_url_futures_um():
    url = _monthly_url("futures_um", "XRPUSDT", "5m", 2024, 7)
    assert url == (
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        "XRPUSDT/5m/XRPUSDT-5m-2024-07.zip"
    )


@pytest.mark.unit
def test_daily_url_spot():
    url = _daily_url("spot", "BTCUSDT", "1h", date(2025, 1, 2))
    assert url == (
        "https://data.binance.vision/data/spot/daily/klines/"
        "BTCUSDT/1h/BTCUSDT-1h-2025-01-02.zip"
    )


@pytest.mark.unit
def test_rest_endpoint():
    assert _endpoint("spot").endswith("/api/v3/klines")
    assert _endpoint("futures_um").endswith("/fapi/v1/klines")
    with pytest.raises(ValueError):
        _endpoint("bogus")


@pytest.mark.unit
def test_interval_tables_consistent():
    # REST에서 쓰는 모든 interval은 아카이브에서도 유효해야 함 (1mo 예외)
    for iv in INTERVAL_TO_MS:
        assert iv in VALID_INTERVALS, f"{iv} not in archive intervals"


# -----------------------------------------------------------------------
# 월/일 이터레이터
# -----------------------------------------------------------------------


@pytest.mark.unit
def test_iter_months_cross_year():
    months = list(_iter_months(date(2024, 11, 1), date(2025, 2, 15)))
    assert months == [(2024, 11), (2024, 12), (2025, 1), (2025, 2)]


@pytest.mark.unit
def test_iter_days_count():
    days = list(_iter_days(date(2024, 1, 1), date(2024, 1, 10)))
    assert len(days) == 10
    assert days[0] == date(2024, 1, 1)
    assert days[-1] == date(2024, 1, 10)


# -----------------------------------------------------------------------
# ZIP 파싱
# -----------------------------------------------------------------------


def _make_binance_zip(rows: list, filename: str = "test.csv") -> bytes:
    """테스트용 바이낸스 klines ZIP 바이트 생성."""
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    for r in rows:
        writer.writerow(r)
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, csv_buf.getvalue())
    return zip_buf.getvalue()


@pytest.mark.unit
def test_parse_zip_to_klines_no_header():
    # 바이낸스 아카이브는 일반적으로 헤더 없음
    rows = [
        # open_time_ms, o, h, l, c, v, close_time_ms, qav, n, tbbav, tbqav, ignore
        ["1717113600000", "0.5200", "0.5300", "0.5190", "0.5250", "1000.5",
         "1717113899999", "500.25", "10", "600", "300", "0"],
        ["1717113900000", "0.5250", "0.5280", "0.5240", "0.5260", "800.0",
         "1717114199999", "400.0", "8", "500", "250", "0"],
    ]
    zip_bytes = _make_binance_zip(rows)
    klines = _parse_zip_to_klines(zip_bytes)
    assert len(klines) == 2
    assert klines[0].open_time_ms == 1717113600000
    assert klines[0].close == 0.5250
    assert klines[1].volume == 800.0


@pytest.mark.unit
def test_parse_zip_to_klines_with_header():
    # 최근 일부 아카이브는 헤더 포함
    rows = [
        ["open_time", "open", "high", "low", "close", "volume",
         "close_time", "qav", "n", "tbbav", "tbqav", "ignore"],
        ["1717113600000", "0.5200", "0.5300", "0.5190", "0.5250", "1000.5",
         "1717113899999", "500.25", "10", "600", "300", "0"],
    ]
    zip_bytes = _make_binance_zip(rows)
    klines = _parse_zip_to_klines(zip_bytes)
    assert len(klines) == 1
    assert klines[0].open == 0.52


# -----------------------------------------------------------------------
# 중복 제거 / CSV 변환
# -----------------------------------------------------------------------


def _mk(ts_ms: int, o=1.0, h=1.0, l=1.0, c=1.0, v=1.0) -> RawKline:
    return RawKline(
        open_time_ms=ts_ms, open=o, high=h, low=l, close=c, volume=v,
        close_time_ms=ts_ms + 1,
    )


@pytest.mark.unit
def test_dedupe_sorted_removes_duplicates():
    klines = [_mk(2000), _mk(1000), _mk(2000), _mk(3000), _mk(1000)]
    out = _dedupe_sorted(klines)
    assert [k.open_time_ms for k in out] == [1000, 2000, 3000]


@pytest.mark.unit
def test_compute_direction():
    assert _compute_direction(1.0, 1.5) == 1
    assert _compute_direction(1.5, 1.0) == -1
    assert _compute_direction(1.0, 1.0) == 0


@pytest.mark.unit
def test_kline_to_csv_row_utc_format():
    # 2024-06-01 00:00:00 UTC = 1717200000
    k = _mk(1717200000000, o=0.5, h=0.6, l=0.4, c=0.55, v=100.0)
    row = _kline_to_csv_row(k)
    assert row[0] == "2024-06-01 00:00:00"
    assert row[6] == 1  # close > open


@pytest.mark.unit
def test_write_algoforge_csv_roundtrip(tmp_path: Path):
    klines = [_mk(1717200000000, 0.5, 0.6, 0.4, 0.55, 100.0)]
    out = tmp_path / "out.csv"
    write_algoforge_csv(klines, out)
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert text.startswith("dt,do,dh,dl,dc,dv,dd")
    # 기존 load_bars_from_csv로 읽을 수 있는지 확인
    from apps.api.db.utils import load_bars_from_csv
    bars, meta = load_bars_from_csv(str(out))
    assert len(bars) == 1
    assert bars[0].close == 0.55
    assert bars[0].direction == 1
