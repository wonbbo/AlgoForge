"""
바이낸스 데이터 수집 모듈

- klines_archive: data.binance.vision의 월/일 ZIP 아카이브에서 대량 백필
- klines_rest: 바이낸스 REST API로 최근 봉 수집 (아카이브에 없는 구간)
- merger: 두 소스를 병합해 중복·갭 없는 CSV 생성
"""
