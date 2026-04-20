"""
AlgoForge 시간대 정책: 사용자·CSV 기준은 KST(Asia/Seoul).

내부 Bar.timestamp 등은 Unix 초(UTC epoch)로 통일한다.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# 한국 표준시 (서머타임 없음)
KST = ZoneInfo("Asia/Seoul")


def kst_day_bounds_ms(start_calendar: date, end_calendar: date) -> tuple[int, int]:
    """
    KST 달력 start_calendar ~ end_calendar (양 끝 날짜 포함)에 해당하는 구간을
    밀리초 epoch [start_ms, end_ms]로 반환.

    - start: 해당 start_calendar 의 00:00:00.000 KST
    - end: 해당 end_calendar 의 23:59:59.999 KST (포함)
    """
    if start_calendar > end_calendar:
        raise ValueError(f"start_calendar > end_calendar: {start_calendar} > {end_calendar}")
    start_dt = datetime.combine(start_calendar, datetime.min.time(), tzinfo=KST)
    end_dt = (
        datetime.combine(end_calendar, datetime.min.time(), tzinfo=KST)
        + timedelta(days=1)
        - timedelta(milliseconds=1)
    )
    return int(start_dt.timestamp() * 1000), int(end_dt.timestamp() * 1000)


def utc_calendar_days_covering_kst_range(start_ms: int, end_ms: int) -> tuple[date, date]:
    """
    [start_ms, end_ms] 구간과 겹치는 UTC 날짜의 최소·최대 (아카이브 ZIP 일자 선택용).
    """
    from datetime import timezone as _tz

    u = _tz.utc
    d0 = datetime.fromtimestamp(start_ms / 1000.0, tz=u).date()
    d1 = datetime.fromtimestamp(end_ms / 1000.0, tz=u).date()
    return d0, d1
