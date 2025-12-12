# AlgoForge ADR v1.0 (Architecture Decision Record)

## 1. 목적
본 ADR은 AlgoForge PRD/TRD를 구현하기 위한 기술 스택 및 아키텍처 선택을 명시한다.
본 문서는 구현 변경 시에도 PRD/TRD의 규칙을 침해하지 않는 범위 내에서만 수정 가능하다.

## 2. 전체 아키텍처 개요
- Web 기반 단일 사용자 연구용 시스템
- Frontend / Backend / Backtest Engine 분리
- 결정성(deterministic) 보장 구조

```
[Frontend] → [API Server] → [Backtest Engine]
                   ↓
                [SQLite]
```

## 3. 기술 스택 결정

### 3.1 Frontend
- Framework: Next.js (App Router)
- UI Library: ShadCN
- Styling: TailwindCSS
- State: React useState / useReducer (MVP)
- Charts: TradingView Lightweight Charts

선정 이유:
- 빠른 프로토타이핑
- 전략 빌더(JSON 기반) 구현 용이
- 장기 유지보수 용이

### 3.2 Backend API
- Framework: FastAPI (Python)
- 역할:
  - Dataset/Strategy/Run 관리
  - Run 실행 트리거
  - 결과 조회 API 제공

### 3.3 Backtest Engine
- Language: Python
- 실행 방식: Backend 내부 워커 또는 Background Task
- 특징:
  - 단일 스레드 실행
  - 결정적 결과 보장
  - 테스트 데이터(A~G) 기반 검증

### 3.4 Database
- SQLite (file-based)
- WAL mode
- PRD/TRD에 정의된 DDL v1.0 사용

## 4. 폴더 구조(권장)
```
algo-forge/
 ├─ apps/
 │   ├─ web/        # Next.js
 │   └─ api/        # FastAPI
 ├─ engine/         # Backtest engine
 ├─ tests/
 └─ docs/
```

## 5. 비결정성 요소 배제 규칙
- 난수 사용 금지
- 병렬 실행 금지
- 시스템 시간 의존 금지
- floating 계산은 Python 기본 float 사용

## 6. 향후 변경 정책
- 기술 스택 변경 가능
- 단, PRD/TRD 규칙 위반 불가
- 변경 시 ADR 버전 증가
