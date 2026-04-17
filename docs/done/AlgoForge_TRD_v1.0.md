# AlgoForge TRD v1.0 FINAL

## 1. 엔진 개요
AlgoForge 엔진은 봉 단위 시뮬레이션 기반의 결정적(deterministic) 백테스트 엔진이다.

## 2. 데이터 처리
- 입력 데이터: CSV (dt, do, dh, dl, dc, dv, dd)
- dt는 오름차순 정렬 필수
- dt은 5분 고정

## 3. 봉 처리 순서
각 봉마다 다음 순서로 처리한다:
1. 기존 포지션 관리
2. SL / TP1 / Reverse 판정
3. 포지션 종료 처리
4. 신규 진입 판정

## 4. TP/SL 판정 규칙
- 도달 판정: high / low
- 체결 가격: close
- 동일 봉에서 복수 이벤트 발생 시 우선순위 적용

## 5. Reverse Signal 평가
- TP1이 발생한 봉에서는 reverse signal을 평가하지 않음
- 다음 봉부터 평가 재개

## 6. 리스크 계산
- risk = |entry_price - stop_loss|
- position_size = (initial_balance * 0.02) / risk
- risk == 0 인 경우:
  - 진입 스킵
  - warning 기록

## 7. TP1 처리
- TP1 도달 시:
  - trade_legs에 TP1 leg 생성 (qty_ratio=0.5)
  - SL을 진입가로 이동
  - TP1 발생 봉에서는 reverse 평가 안 함

## 8. 종료 처리
- SL, BE, Reverse 종료 시:
  - FINAL leg 생성
  - qty_ratio=잔여 수량
  - trade 종료

## 9. trade_legs 규칙
- 하나의 trade_id에 TP1 + FINAL 최대 2개 leg
- SL로 전량 종료 시 leg는 1개(FINAL)

## 10. Metrics 산출
- trade 단위 기준으로 계산
- TP1 발생 여부, BE 종료 여부 기록

## 11. Score 계산
- metrics 입력 기반 score(0~100) 산출
- grade 매핑:
  - S: 85~100
  - A: 70~84
  - B: 55~69
  - C: 40~54
  - D: <40

## 12. Run 실행 정책
- run은 생성 후 단방향 실행
- 재실행은 항상 새로운 run 생성으로 처리
- 기존 결과 수정 없음

## 13. 오류 처리
- 치명적 오류 발생 시 run 상태를 FAILED로 전환
- warning은 run_artifacts에 기록

## 14. 결정성 보장
- 동일 dataset_hash + strategy_hash + engine_version → 동일 결과
