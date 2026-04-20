# AlgoForge 시간·타임존 정책 (KST 고정)

## 원칙

| 구분 | 규칙 |
|------|------|
| **내부 저장** | `Bar.timestamp`, 거래 시각 등은 **Unix 초(UTC epoch)**. “순간”만 저장하며 DB에 타임존 필드는 없음. |
| **CSV 컬럼 `dt`** | **한국 표준시(KST, `Asia/Seoul`, UTC+9)** 의 벽시계를 `YYYY-MM-DD HH:MM:SS` 로 기록. 타임존 접미사 없음. |
| **바이낸스 수집 기간** | UI/API의 `start_date` / `end_date` (`YYYY-MM-DD`)는 **KST 달력 기준** (해당일 00:00:00 KST ~ 해당일 포함 마지막 ms). |
| **화면 표시** | 사용자에게 보이는 시각은 **항상 KST** (`Intl` 등에 `timeZone: 'Asia/Seoul'`). |

## 바이낸스 API

- 캔들 `open_time`은 밀리초 epoch(UTC). 내부는 그대로 두고, CSV `dt` 문자열로 쓸 때만 **KST로 변환**해 표기한다.

## 업로드 CSV

- `dt`는 **KST**로 해석해 epoch로 변환한다. (레거시 UTC로 만든 파일은 재수집·재업로드 권장.)

## 관련 코드

- 파싱: `apps/api/db/utils.py` — `load_bars_from_csv`, `save_bars_to_csv`
- 수집: `engine/data/binance/merger.py` — `_kline_to_csv_row`, `fetch_and_merge` 경계
- 표시: `apps/web/lib/utils.ts` — `formatTimestamp`, `formatDate`
