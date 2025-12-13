# AlgoForge 전략 빌더 구현 문서

## 📚 문서 개요

이 디렉토리는 AlgoForge 전략 빌더 UI 구현 과정과 결과를 문서화합니다.

---

## 📂 문서 구조

### 구현 가이드
- **`AlgoForge_Strategy_Builder_Implementation_Guide_v1.0.md`** (상위 디렉토리)
  - 전체 구현 가이드
  - 아키텍처 및 설계
  - 단계별 구현 계획

### Phase 1: 프로젝트 설정 및 기본 구조
- **`Phase1_Implementation_Report.md`**
  - 상세 구현 내용
  - 타입 시스템
  - Validation 로직
  - Draft → JSON 변환

- **`Phase1_Summary.md`**
  - 한눈에 보는 요약
  - 핵심 기능
  - 검증 결과

- **`Phase1_Checklist.md`**
  - 구현 체크리스트
  - 진행 상황 추적

- **`Phase1_Quick_Start.md`**
  - 빠른 시작 가이드
  - 실행 방법

### Phase 2: 전략 빌더 UI 컴포넌트 구현
- **`Phase2_Implementation_Report.md`**
  - 상세 구현 내용
  - 컴포넌트별 설명
  - UI/UX 설계

- **`Phase2_Summary.md`**
  - 한눈에 보는 요약
  - 핵심 기능
  - 데모 시나리오

### Phase 3: 테스트 및 디버깅
- **`Phase3_Implementation_Report.md`**
  - 상세 구현 내용
  - 테스트 전략
  - 커버리지 리포트

- **`Phase3_Summary.md`**
  - 한눈에 보는 요약
  - 테스트 결과
  - 결정성 보장

### Phase 4: 프론트엔드-백엔드 통합
- **`Phase4_Implementation_Report.md`**
  - 상세 구현 내용
  - API 연동
  - 통합 테스트

- **`Phase4_Summary.md`**
  - 한눈에 보는 요약
  - 핵심 기능
  - 테스트 시나리오

### Phase 5: Run 실행 및 결과 시각화
- **`Phase5_Implementation_Report.md`**
  - 상세 구현 내용
  - 차트 컴포넌트
  - Trade 상세 페이지

- **`Phase5_Summary.md`**
  - 한눈에 보는 요약
  - 핵심 기능
  - 테스트 시나리오

### Phase 6: 고급 기능 및 UI 개선
- **`Phase6_Implementation_Report.md`**
  - 상세 구현 내용
  - Reverse 설정
  - Hook 설정 (MVP 비활성화)
  - 지표 ID 편집기
  - Validation 강화

- **`Phase6_Summary.md`**
  - 한눈에 보는 요약
  - 핵심 기능
  - 테스트 시나리오

### Phase 7: 전략 테스트 및 최적화
- **`Phase7_Implementation_Report.md`**
  - 상세 구현 내용
  - 템플릿 저장/불러오기
  - 전략 복제
  - 전략 비교
  - 성능 최적화

- **`Phase7_Summary.md`**
  - 한눈에 보는 요약
  - 핵심 기능
  - 테스트 시나리오

### 설계 문서
- **`AlgoForge_Draft_to_JSON_Rules.md`**
  - Draft → JSON 변환 규칙
  - Canonicalization

- **`AlgoForge_UI_Component_Design.md`**
  - UI 컴포넌트 설계
  - 컴포넌트 구조

- **`AlgoForge_UI_Wireframe.md`**
  - UI 와이어프레임
  - 레이아웃 설계

---

## 🚀 빠른 시작

### 1. 개발 서버 실행
```bash
cd apps/web
pnpm install
pnpm dev
```

### 2. 브라우저 접근
```
http://localhost:3000/strategies/builder
```

### 3. 전략 작성
1. 전략 이름 입력
2. Step 1: 지표 선택
3. Step 2: 진입 조건 구성
4. Step 3: 손절 방식 선택
5. JSON Preview 확인
6. 저장 (복사 또는 다운로드)

---

## 📊 구현 현황

### Phase 1: 프로젝트 설정 ✅
- ✅ Next.js 프로젝트 설정
- ✅ ShadCN UI 컴포넌트 추가
- ✅ 타입 정의 (strategy-draft.ts)
- ✅ Validation 로직 (draft-validation.ts)
- ✅ Draft → JSON 변환 (draft-to-json.ts)
- ✅ Canonicalization 구현

**생성 파일**: 8개 (783줄)

### Phase 2: UI 컴포넌트 구현 ✅
- ✅ StrategyHeader (전략 헤더)
- ✅ Step1_IndicatorSelector (지표 선택)
- ✅ ConditionRow (조건 입력)
- ✅ Step2_EntryBuilder (진입 조건)
- ✅ Step3_StopLossSelector (손절 방식)
- ✅ JsonPreviewPanel (JSON 미리보기)
- ✅ StepWizard (Step 통합)
- ✅ page.tsx (메인 페이지)
- ✅ radio-group.tsx (RadioGroup 컴포넌트)

**생성 파일**: 9개 (1,250줄)

### Phase 3: 테스트 및 디버깅 ✅
- ✅ Jest 설정
- ✅ 단위 테스트 (15개)
- ✅ 통합 테스트 (19개)
- ✅ Canonicalization 테스트 (11개)
- ✅ 유틸 테스트 (5개)
- ✅ 컴포넌트 테스트 (3개)

**생성 파일**: 8개 (1,480줄)

### Phase 4: 프론트엔드-백엔드 통합 ✅
- ✅ Toast 알림 시스템 (Sonner)
- ✅ 전략 빌더 저장 기능
- ✅ 전략 목록 페이지 개선
- ✅ 전략 상세 보기 페이지
- ✅ 네비게이션 플로우
- ✅ 백엔드 API 서버 테스트
- ✅ 통합 테스트 (6개 시나리오)

**수정/생성 파일**: 5개 (~400줄)

### Phase 5: Run 실행 및 결과 시각화 ✅
- ✅ TradingView Lightweight Charts 통합
- ✅ Equity Curve 차트 (자산 변화)
- ✅ Drawdown 차트 (손실폭)
- ✅ Trade 상세 페이지
- ✅ Toast 알림 추가
- ✅ Run 상세 페이지 개선

**신규/수정 파일**: 6개 (~570줄)

### Phase 3: 테스트 및 디버깅 ✅
- ✅ 단위 테스트 (52개)
- ✅ 통합 테스트
- ✅ 커버리지 80% 이상
- ✅ 결정성 보장 테스트

### Phase 4: 프론트엔드-백엔드 통합 ✅
- ✅ 전략 빌더 저장 기능 (API 연동)
- ✅ Toast 알림 시스템
- ✅ 전략 목록 페이지 개선
- ✅ 전략 상세 보기 페이지
- ✅ 네비게이션 플로우
- ✅ 통합 테스트

### Phase 5: Run 실행 및 결과 시각화 ✅
- ✅ TradingView Lightweight Charts 통합
- ✅ Equity Curve 차트 구현
- ✅ Drawdown 차트 구현
- ✅ Trade 상세 페이지 구현
- ✅ Toast 알림 추가
- ✅ Run 상세 페이지 개선

### Phase 6: 고급 기능 및 UI 개선 ✅
- ✅ Reverse 설정 컴포넌트 구현
- ✅ Hook 설정 컴포넌트 구현 (MVP 비활성화)
- ✅ 지표 ID 편집기 구현
- ✅ Validation 규칙 강화
- ✅ Switch 컴포넌트 추가
- ✅ 빌드 및 테스트 완료

### Phase 7: 전략 테스트 및 최적화 ✅
- ✅ 전략 템플릿 저장/불러오기
- ✅ 전략 복제 기능
- ✅ 전략 비교 기능
- ✅ 성능 최적화 (메모이제이션)

### Phase 8: 테스트 ⏳
- ⏳ 단위 테스트
- ⏳ 통합 테스트
- ⏳ E2E 테스트

### Phase 9: 문서화 ⏳
- ⏳ 사용자 가이드
- ⏳ API 문서
- ⏳ 개발자 가이드

---

## 🎯 핵심 기능

### 1. JSON 지식 불필요
- 카드 기반 지표 선택
- 문장형 조건 입력
- 드롭다운 선택
- 실시간 JSON 생성

### 2. 실시간 피드백
- Validation 에러 즉시 표시
- JSON Preview 자동 업데이트
- 저장 버튼 활성화/비활성화
- 명확한 안내 메시지

### 3. 사용자 친화적
- Step-by-Step 입력
- 아이콘 및 카테고리 표시
- 팁 및 안내 메시지
- 에러 방지

---

## 📖 문서 읽기 순서

### 처음 시작하는 경우
1. `Phase1_Quick_Start.md` - 빠른 시작
2. `Phase1_Summary.md` - Phase 1 요약
3. `Phase2_Summary.md` - Phase 2 요약
4. `Phase3_Summary.md` - Phase 3 요약
5. `Phase4_Summary.md` - Phase 4 요약
6. `Phase5_Summary.md` - Phase 5 요약
7. `Phase6_Summary.md` - Phase 6 요약

### 상세 내용이 필요한 경우
1. `Phase1_Implementation_Report.md` - Phase 1 상세
2. `Phase2_Implementation_Report.md` - Phase 2 상세
3. `Phase3_Implementation_Report.md` - Phase 3 상세
4. `Phase4_Implementation_Report.md` - Phase 4 상세
5. `Phase5_Implementation_Report.md` - Phase 5 상세
6. `Phase6_Implementation_Report.md` - Phase 6 상세
7. `AlgoForge_Strategy_Builder_Implementation_Guide_v1.0.md` - 전체 가이드

### 설계 문서가 필요한 경우
1. `AlgoForge_UI_Wireframe.md` - UI 와이어프레임
2. `AlgoForge_UI_Component_Design.md` - 컴포넌트 설계
3. `AlgoForge_Draft_to_JSON_Rules.md` - 변환 규칙

---

## 🔑 주요 개념

### Draft State
- **정의**: UI 전용 상태
- **목적**: 사용자 친화적인 입력
- **변환**: Draft → Strategy JSON

### Strategy JSON
- **정의**: 백엔드 전송용 JSON
- **규격**: Schema v1.0 준수
- **결정성**: 동일 Draft → 동일 hash

### Validation
- **시점**: Draft 업데이트 시마다
- **규칙**: PRD/TRD 준수
- **결과**: 에러 목록 반환

### Canonicalization
- **목적**: 동일 hash 보장
- **방법**: meta 제외, key 정렬
- **결과**: SHA-256 hash

---

## 🛠️ 기술 스택

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript (strict mode)
- **UI Library**: ShadCN UI
- **Styling**: TailwindCSS
- **Icons**: lucide-react
- **Package Manager**: pnpm

### Backend (예정)
- **Framework**: FastAPI
- **Database**: SQLite
- **Engine**: Python

---

## 📁 파일 구조

```
AlgoForge/
├─ apps/web/
│  ├─ app/
│  │  ├─ layout.tsx                          # Toaster 추가
│  │  └─ strategies/
│  │     ├─ page.tsx                         # 전략 목록 (Toast 추가)
│  │     ├─ [id]/
│  │     │  └─ page.tsx                      # 전략 상세 (신규)
│  │     └─ builder/
│  │        ├─ page.tsx                      # 전략 빌더 (API 연동)
│  │        └─ components/
│  │           ├─ StrategyHeader.tsx         # 전략 헤더 (isSaving)
│  │           ├─ Step1_IndicatorSelector.tsx
│  │           ├─ ConditionRow.tsx
│  │           ├─ Step2_EntryBuilder.tsx
│  │           ├─ Step3_StopLossSelector.tsx
│  │           ├─ JsonPreviewPanel.tsx
│  │           └─ StepWizard.tsx
│  ├─ components/ui/
│  │  ├─ button.tsx
│  │  ├─ card.tsx
│  │  ├─ input.tsx
│  │  ├─ select.tsx
│  │  ├─ tabs.tsx
│  │  ├─ alert.tsx
│  │  ├─ label.tsx
│  │  ├─ badge.tsx
│  │  └─ radio-group.tsx
│  ├─ lib/
│  │  ├─ strategy-draft-utils.ts
│  │  ├─ draft-validation.ts
│  │  ├─ draft-to-json.ts
│  │  └─ api-client.ts                       # API 클라이언트
│  ├─ types/
│  │  └─ strategy-draft.ts
│  └─ __tests__/                             # 테스트 (52개)
│     ├─ draft-validation.test.ts
│     ├─ draft-to-json.test.ts
│     ├─ canonicalization.test.ts
│     ├─ components/
│     │  └─ ConditionRow.test.tsx
│     └─ utils/
│        └─ strategy-draft-utils.test.ts
└─ docs/step2/
   ├─ README.md                               # 이 파일
   ├─ Phase1_Implementation_Report.md
   ├─ Phase1_Summary.md
   ├─ Phase1_Checklist.md
   ├─ Phase1_Quick_Start.md
   ├─ Phase2_Implementation_Report.md
   ├─ Phase2_Summary.md
   ├─ Phase3_Implementation_Report.md
   ├─ Phase3_Summary.md
   ├─ Phase4_Implementation_Report.md
   ├─ Phase4_Summary.md
   ├─ Phase5_Implementation_Report.md         # 신규
   ├─ Phase5_Summary.md                       # 신규
   ├─ AlgoForge_Draft_to_JSON_Rules.md
   ├─ AlgoForge_UI_Component_Design.md
   └─ AlgoForge_UI_Wireframe.md
```

---

## ⚠️ 주의 사항

### 절대 금지 (MUST NOT)
1. ❌ Strategy JSON Schema v1.0 구조 변경
2. ❌ PRD/TRD 규칙 단순화
3. ❌ Draft 자동 보정
4. ❌ 비결정적 요소 추가
5. ❌ Validation 규칙 완화

### 필수 준수 (MUST)
1. ✅ Draft State는 UI 전용
2. ✅ Validation 실패 시 JSON 생성 금지
3. ✅ 동일 Draft → 동일 strategy_hash
4. ✅ 명확한 Validation 및 에러 메시지
5. ✅ JSON Preview는 Read-only

---

## 🔗 관련 문서

### 상위 문서
- `../AlgoForge_PRD_v1.0.md` - 제품 요구사항 정의
- `../AlgoForge_TRD_v1.0.md` - 기술 요구사항 정의
- `../AlgoForge_ADR_v1.0.md` - 아키텍처 결정 기록

### Cursor 규칙
- `.cursor/rules/backtest-engine-rules.mdc` - 백테스트 엔진 규칙
- `.cursor/rules/nextjs-usage.mdc` - Next.js 사용 원칙
- `.cursor/rules/trading-model-rules.mdc` - 거래 모델 규칙
- `.cursor/rules/ui-design-rules.mdc` - UI 디자인 원칙

---

## 📞 문의 및 지원

### 이슈 리포팅
- 버그 발견 시: GitHub Issues
- 기능 제안: GitHub Discussions

### 개발 가이드
- 코드 품질: `.cursor/rules/` 참조
- 커밋 메시지: `feat:`, `fix:`, `refactor:` 등
- 테스트: 모든 핵심 로직 테스트 필수

---

## 🎉 마치며

AlgoForge 전략 빌더는 **JSON 지식 없이도 전략을 작성**할 수 있는 
강력하고 직관적인 도구입니다.

Phase 1과 Phase 2를 통해 완전한 UI가 구현되었으며,
이제 백엔드 구현 및 API 연동을 통해 실제 전략 백테스팅이 가능해집니다.

**Happy Coding!** 🚀

---

**최종 업데이트**: 2025-12-13  
**버전**: 4.0  
**작성자**: Cursor AI
