# AlgoForge

전략 개발·비교·개선 목적의 웹 기반 백테스팅 도구

## 프로젝트 개요

AlgoForge는 개인 연구자를 위한 **결정적이고 재현 가능한 백테스트 결과**를 제공하는 연구용 도구입니다.

### 핵심 가치
- **결정성(Deterministic)**: 동일 입력 → 항상 동일 출력
- **재현성(Reproducibility)**: 언제든 동일한 결과 재생산
- **비교 가능성(Comparability)**: 전략 간 구조적 품질 비교

## 기술 스택

### Backend
- **Engine**: Python 3.10+
- **API**: FastAPI
- **Database**: SQLite (WAL mode)

### Frontend
- **Framework**: Next.js (App Router)
- **UI**: ShadCN + TailwindCSS
- **Charts**: TradingView Lightweight Charts
- **Package Manager**: pnpm

## 프로젝트 구조

```
AlgoForge/
├─ engine/          # 백테스트 엔진 (핵심)
├─ apps/
│  ├─ api/          # FastAPI 백엔드
│  └─ web/          # Next.js 프론트엔드
├─ tests/           # 테스트 및 테스트 데이터
├─ db/              # SQLite 데이터베이스
└─ docs/            # 문서 (PRD, TRD, ADR, 구현 가이드)
```

## 시작하기

### Python 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=engine --cov=apps/api
```

### API 서버 실행

```bash
# 방법 1: 시작 스크립트 사용 (권장)
# Windows:
start_api_server.bat

# macOS/Linux:
./start_api_server.sh

# 방법 2: 직접 실행 (프로젝트 루트에서)
python -m uvicorn apps.api.main:app --reload --port 8000
```

**API 문서**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Frontend 개발 서버 (Phase 5 이후)

```bash
cd apps/web
pnpm install
pnpm dev
```

## 개발 로드맵

### ✅ Phase 1: 백테스트 엔진 핵심 (완료)
- ✅ 데이터 모델 정의 (Bar, Position, Trade, TradeLeg)
- ✅ 봉 처리 엔진 구현 (BacktestEngine)
- ✅ 리스크 관리 로직 (RiskManager)
- ✅ Metrics 계산 (MetricsCalculator)
- ✅ 단위 테스트 작성 및 검증 (6개 테스트 모두 통과)
- ✅ 결정성 검증 완료
- 📄 [Phase 1 구현 결과보고서](docs/step1/Phase1_Implementation_Report.md)

### ✅ Phase 2: 테스트 데이터 및 검증 (완료)
- ✅ 테스트 데이터 A~G 생성 (7개)
- ✅ 단위 테스트 확장 (11개 테스트 모두 통과)
- ✅ 엣지 케이스 검증
- ✅ 결정성 검증 완료
- 📄 [Phase 2 구현 결과보고서](docs/step1/Phase2_Implementation_Report.md)

### ✅ Phase 3: 데이터베이스 (완료)
- ✅ SQLite 스키마 설계 및 검증
- ✅ Database 연결 클래스 구현
- ✅ Repository 클래스 6개 구현 (CRUD 로직)
- ✅ 데이터베이스 유틸리티 함수 구현
- ✅ 통합 테스트 작성 (18개 테스트 모두 통과)
- ✅ 해시 기반 결정성 보장
- 📄 [Phase 3 구현 결과보고서](docs/step1/Phase3_Implementation_Report.md)

### ✅ Phase 4: FastAPI 백엔드 (완료)
- ✅ Pydantic Schemas 정의 (Request/Response 모델)
- ✅ FastAPI 메인 애플리케이션 구성
- ✅ Dataset API Router 구현 (4개 엔드포인트)
- ✅ Strategy API Router 구현 (4개 엔드포인트)
- ✅ Run API Router 구현 (5개 엔드포인트, Background Task 포함)
- ✅ 에러 핸들링 및 유틸리티 구현
- ✅ API 통합 테스트 작성 및 검증
- 📄 [Phase 4 구현 결과보고서](docs/step1/Phase4_Implementation_Report.md)

### Phase 5: Next.js 프론트엔드 ⭐⭐
- 전략 빌더 UI
- 결과 시각화

### Phase 6: 통합 및 배포 ⭐⭐
- E2E 테스트
- 성능 최적화

## 문서

상세한 구현 가이드는 다음 문서를 참조하세요:

### 기획 문서
- [PRD v1.0](docs/AlgoForge_PRD_v1.0.md) - 제품 요구사항 명세
- [TRD v1.0](docs/AlgoForge_TRD_v1.0.md) - 기술 요구사항 명세
- [ADR v1.0](docs/AlgoForge_ADR_v1.0.md) - 아키텍처 결정 기록
- [Implementation Guide v1.0](docs/AlgoForge_Implementation_Guide_v1.0.md) - 구현 가이드

### 구현 보고서

- [Phase 1 구현 결과보고서](docs/step1/Phase1_Implementation_Report.md) - 백테스트 엔진 핵심 구현 완료
- [Phase 2 구현 결과보고서](docs/step1/Phase2_Implementation_Report.md) - 테스트 데이터 및 검증 완료
- [Phase 3 구현 결과보고서](docs/step1/Phase3_Implementation_Report.md) - 데이터베이스 구현 완료
- [Phase 4 구현 결과보고서](docs/step1/Phase4_Implementation_Report.md) - FastAPI 백엔드 구현 완료

## 개발 원칙

### 절대 규칙 (MUST)
1. PRD/TRD의 규칙은 절대 변경하거나 단순화하지 마세요
2. 모든 구현은 결정적(deterministic)이어야 합니다
3. 테스트 데이터 A~G를 모두 통과해야 합니다
4. 봉 단위 시뮬레이션 기반 엔진
5. Close Fill 체결만 사용

### 비결정성 요소 배제
- ❌ 난수 사용 금지 (random, uuid)
- ❌ 병렬 실행 금지 (멀티스레드, 멀티프로세스)
- ❌ 시스템 시간 의존 금지 (datetime.now())
- ✅ Python 기본 float 사용
- ✅ 단일 스레드 순차 실행

## 라이선스

이 프로젝트는 개인 연구용 도구입니다.

## 기여

이 프로젝트는 개인 프로젝트입니다.

---

**Good Luck!** 🚀

