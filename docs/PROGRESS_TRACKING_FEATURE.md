# 백테스트 진행률 추적 기능

## 개요

백테스트 실행 중 진행 상황을 프론트엔드에서 실시간으로 확인할 수 있도록 진행률 추적 기능을 구현했습니다.

## 구현 내용

### 1. 데이터베이스 스키마 변경

**파일**: `db/schema.sql`

`runs` 테이블에 진행률 추적을 위한 컬럼 추가:
- `progress_percent` (REAL): 진행률 (0~100)
- `processed_bars` (INTEGER): 처리된 봉 개수
- `total_bars` (INTEGER): 전체 봉 개수

**마이그레이션**: `db/migrations/001_add_progress_columns.sql`

### 2. 백테스트 엔진 수정

**파일**: `engine/core/backtest_engine.py`

- `BacktestEngine` 생성자에 `progress_callback` 파라미터 추가
- `run()` 메서드에서 1% 단위로 진행률 콜백 호출
- 업데이트 주기: 최소 100개 봉마다 또는 전체 봉의 1%마다

```python
engine = BacktestEngine(
    initial_balance=10000,
    strategy_func=strategy_func,
    progress_callback=lambda processed, total: print(f"{processed}/{total}")
)
```

### 3. Repository 수정

**파일**: `apps/api/db/repositories.py`

`RunRepository`에 `update_progress()` 메서드 추가:

```python
run_repo.update_progress(
    run_id=1,
    processed_bars=500,
    total_bars=1000
)
```

### 4. API 수정

**파일**: `apps/api/routers/runs.py`

- `execute_backtest()` 함수에 진행률 콜백 연결
- 백테스트 실행 중 주기적으로 DB에 진행률 업데이트

**파일**: `apps/api/schemas/run.py`

`RunResponse`에 진행률 필드 추가:
- `progress_percent`: 진행률 (0~100)
- `processed_bars`: 처리된 봉 개수
- `total_bars`: 전체 봉 개수

### 5. Frontend 구현

**파일**: `apps/web/app/runs/components/RunProgressMonitor.tsx`

진행률 모니터링 컴포넌트:
- 1초마다 API 폴링하여 진행률 업데이트
- RUNNING 상태일 때 진행 바 표시
- 완료 시 자동으로 폴링 중단

**파일**: `apps/web/app/runs/page.tsx`

Run 목록 테이블에 진행률 모니터 통합:
- RUNNING 상태인 Run에 진행률 바 표시
- 다른 상태는 기존 Badge 표시 유지

**파일**: `apps/web/lib/types.ts`

`Run` 인터페이스에 진행률 필드 추가

## 동작 방식

```
[Frontend] → [Polling (1초)] → [API GET /api/runs/{id}]
                                        ↓
                                   [Database]
                                        ↑
[BacktestEngine] → [Callback (1%)] → [API] → [DB Update]
```

### 흐름 설명

1. **Run 생성**: 사용자가 Run 생성 요청
2. **백테스트 시작**: Background Task로 백테스트 실행
3. **진행률 업데이트**: 엔진이 1% 단위로 DB에 진행률 업데이트
4. **Frontend 폴링**: 1초마다 Run 상태 조회
5. **실시간 표시**: 진행 바로 시각적 피드백
6. **자동 완료**: 완료 시 폴링 중단 및 데이터 새로고침

## 테스트 방법

### 1. 마이그레이션 적용

```bash
cd /home/wonbbo/algoforge
python db/apply_migration.py
```

### 2. API 서버 시작

```bash
cd apps/api
uvicorn main:app --reload
```

### 3. Frontend 서버 시작

```bash
cd apps/web
pnpm dev
```

### 4. Run 생성 및 확인

1. 브라우저에서 `http://localhost:5001/runs` 접속
2. "Run 생성" 버튼 클릭
3. 데이터셋과 전략 선택 후 실행
4. 테이블에서 진행률 바가 실시간으로 업데이트되는 것 확인

### 5. 예상 결과

- **PENDING**: "대기 중" 표시
- **RUNNING**: 진행률 바와 백분율 표시
  - 예: `실행 중 45.3%`
  - 하단에 `4530 / 10000 봉 처리됨`
- **COMPLETED**: "완료" 표시 (녹색)
- **FAILED**: "실행 실패" 표시 (빨간색)

## 성능 고려사항

### DB 업데이트 빈도
- **기본**: 1% 단위 (총 100회)
- **최소**: 100개 봉마다
- **이유**: DB 부하를 최소화하면서 충분한 실시간성 제공

### Frontend 폴링 주기
- **주기**: 1초
- **조건**: RUNNING 상태일 때만
- **자동 중단**: COMPLETED 또는 FAILED 시

### 확장 가능성
향후 필요시 다음과 같이 개선 가능:
1. **Server-Sent Events (SSE)**: 더 실시간성이 필요한 경우
2. **WebSocket**: 양방향 통신이 필요한 경우
3. **환경 변수**: 업데이트 빈도를 설정 파일로 제어

## 주의사항

1. **결정성 유지**: 진행률 업데이트는 백테스트 결과에 영향을 주지 않음
2. **DB 트랜잭션**: 진행률 업데이트 실패해도 백테스트는 계속 진행
3. **폴링 최적화**: RUNNING 상태가 아니면 폴링하지 않음

## 파일 변경 목록

### Backend
- `db/schema.sql` - 스키마 업데이트
- `db/migrations/001_add_progress_columns.sql` - 마이그레이션
- `db/apply_migration.py` - 마이그레이션 적용 스크립트
- `engine/core/backtest_engine.py` - 진행률 콜백 추가
- `apps/api/db/repositories.py` - update_progress 메서드 추가
- `apps/api/routers/runs.py` - 콜백 연결
- `apps/api/schemas/run.py` - RunResponse 필드 추가

### Frontend
- `apps/web/app/runs/components/RunProgressMonitor.tsx` - 진행률 컴포넌트 (신규)
- `apps/web/app/runs/page.tsx` - 컴포넌트 통합
- `apps/web/lib/types.ts` - Run 타입 업데이트

## 버전 정보

- **구현일**: 2025-12-13
- **엔진 버전**: 1.0.0
- **호환성**: 모든 기존 Run과 호환

