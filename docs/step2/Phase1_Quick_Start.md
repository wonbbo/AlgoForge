# Phase 1 Quick Start Guide

## 🚀 빠른 시작

### 1. 개발 서버 실행

```bash
# 프로젝트 루트에서
cd apps/web

# 의존성 설치 (처음 한 번만)
pnpm install

# 개발 서버 실행
pnpm dev
```

개발 서버가 `http://localhost:3000`에서 실행됩니다.

---

## 📍 전략 빌더 접근

### 방법 1: UI에서 접근
1. 브라우저에서 `http://localhost:3000` 열기
2. 좌측 네비게이션에서 "전략" 클릭
3. "전략 빌더 (UI)" 버튼 클릭

### 방법 2: 직접 URL
브라우저에서 `http://localhost:3000/strategies/builder` 열기

---

## 📂 프로젝트 구조

```
AlgoForge/
├─ apps/
│  └─ web/                             # Next.js Frontend
│     ├─ app/
│     │  └─ strategies/
│     │     ├─ page.tsx                # 전략 목록 페이지
│     │     └─ builder/                # ✨ 전략 빌더 (Phase 1)
│     │        ├─ page.tsx             # 빌더 메인 페이지
│     │        ├─ components/          # 빌더 컴포넌트 (Phase 2)
│     │        └─ README.md
│     ├─ components/
│     │  └─ ui/                        # ShadCN UI 컴포넌트
│     │     ├─ button.tsx
│     │     ├─ card.tsx
│     │     ├─ select.tsx              # ✨ Phase 1 추가
│     │     ├─ tabs.tsx                # ✨ Phase 1 추가
│     │     └─ alert.tsx               # ✨ Phase 1 추가
│     ├─ lib/                          # 유틸리티 함수
│     │  ├─ strategy-draft-utils.ts   # ✨ Phase 1 추가
│     │  ├─ draft-validation.ts       # ✨ Phase 1 추가
│     │  └─ draft-to-json.ts          # ✨ Phase 1 추가
│     └─ types/                        # TypeScript 타입
│        └─ strategy-draft.ts          # ✨ Phase 1 추가
└─ docs/
   └─ step2/                           # Phase 1 문서
      ├─ Phase1_Implementation_Report.md
      ├─ Phase1_Checklist.md
      └─ Phase1_Quick_Start.md         # 이 파일
```

---

## 🧪 Phase 1 검증

### 1. 페이지 접근 확인
```
✅ http://localhost:3000/strategies/builder 접근 가능
✅ "Phase 1 구현 완료" 메시지 표시
```

### 2. 타입 시스템 확인
```bash
# TypeScript 타입 체크
cd apps/web
pnpm tsc --noEmit
```

예상 결과: **에러 없음**

### 3. Linting 확인
```bash
# ESLint 실행
cd apps/web
pnpm lint
```

예상 결과: **에러 없음**

---

## 📋 Phase 1 구현 내용

### ✅ 완료된 항목

1. **UI 컴포넌트**
   - Select 컴포넌트 (165 lines)
   - Tabs 컴포넌트 (48 lines)
   - Alert 컴포넌트 (60 lines)

2. **타입 정의**
   - StrategyDraft 타입 시스템
   - Validation 타입
   - Strategy JSON 타입

3. **유틸리티 함수**
   - Draft 생성 및 조작
   - Validation 로직
   - Draft → JSON 변환
   - Canonicalization
   - Hash 계산

4. **폴더 구조**
   - 전략 빌더 디렉토리
   - 컴포넌트 디렉토리
   - 문서 구조

5. **UI 통합**
   - 전략 페이지에 빌더 버튼 추가
   - 라우팅 연결

---

## 🔧 개발 팁

### TypeScript 자동 완성
VSCode에서 타입 자동 완성을 활용하세요:
- `StrategyDraft` 타입 임포트 후 자동 완성
- Validation 함수 사용 시 에러 타입 확인
- Draft → JSON 변환 시 타입 안전성 보장

### 핫 리로딩
개발 서버 실행 중 파일 수정 시 자동으로 페이지가 새로고침됩니다.

---

## 🐛 문제 해결

### 포트 충돌 (3000번 포트 사용 중)
```bash
# 다른 포트로 실행
pnpm dev -- -p 3001
```

### 의존성 에러
```bash
# node_modules 삭제 후 재설치
rm -rf node_modules
pnpm install
```

### 타입 에러
```bash
# TypeScript 캐시 삭제
rm -rf .next
pnpm dev
```

---

## 📖 참조 문서

### 구현 가이드
- `AlgoForge_Strategy_Builder_Implementation_Guide_v1.0.md`
- `Phase1_Implementation_Report.md`
- `Phase1_Checklist.md`

### 규칙 문서
- `AlgoForge_PRD_v1.0.md`
- `AlgoForge_TRD_v1.0.md`
- `AlgoForge_ADR_v1.0.md`

---

## 🎯 다음 단계: Phase 2

Phase 2에서는 실제 UI 컴포넌트를 구현합니다:

1. **StrategyHeader** (0.5일)
   - 전략 이름/설명 입력
   - 저장/실행 버튼
   - Validation 에러 표시

2. **Step1_IndicatorSelector** (1일)
   - 지표 카탈로그
   - 지표 추가/삭제
   - 파라미터 설정

3. **Step2_EntryBuilder** (2일)
   - 롱/숏 조건 구성
   - ConditionRow 통합
   - 조건 추가/삭제

4. **Step3_StopLossSelector** (0.5일)
   - 손절 방식 선택
   - 파라미터 입력

5. **JsonPreviewPanel** (0.5일)
   - 실시간 JSON 미리보기
   - 복사/다운로드 기능

6. **StepWizard** (0.5일)
   - Step 관리
   - 네비게이션

---

## ✅ Phase 1 완료 확인

- [x] 개발 서버 실행 가능
- [x] 전략 빌더 페이지 접근 가능
- [x] TypeScript 타입 체크 통과
- [x] Linting 통과
- [x] 모든 파일 생성 완료
- [x] 문서화 완료

---

**Status**: ✅ Phase 1 완료  
**Ready for**: Phase 2 구현

**실행 확인**:
```bash
cd apps/web
pnpm install
pnpm dev
# → http://localhost:3000/strategies/builder 접근
```

