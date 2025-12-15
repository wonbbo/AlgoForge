# 전략 빌더 (Strategy Builder)

## 개요

AlgoForge 전략 빌더는 JSON 지식 없이도 직관적으로 전략을 만들 수 있는 UI를 제공합니다.

## 현재 상태

### Phase 1 ✅ (완료)
- [x] 프로젝트 기본 설정
- [x] ShadCN UI 컴포넌트 추가
- [x] 타입 정의 (Draft State)
- [x] Validation 로직
- [x] Draft → JSON 변환 로직
- [x] 폴더 구조 생성

### Phase 2 ⏳ (예정)
- [ ] StrategyHeader 컴포넌트
- [ ] Step1_IndicatorSelector 컴포넌트
- [ ] Step2_EntryBuilder 컴포넌트
- [ ] ConditionRow 컴포넌트
- [ ] Step3_StopLossSelector 컴포넌트
- [ ] JsonPreviewPanel 컴포넌트
- [ ] StepWizard 통합

## 폴더 구조

```
app/strategies/builder/
├─ page.tsx                    # 메인 페이지
├─ components/                 # 빌더 컴포넌트
│  ├─ StrategyHeader.tsx       # (Phase 2)
│  ├─ StepWizard.tsx           # (Phase 2)
│  ├─ Step1_IndicatorSelector.tsx
│  ├─ Step2_EntryBuilder.tsx
│  ├─ Step3_StopLossSelector.tsx
│  ├─ ConditionRow.tsx
│  └─ JsonPreviewPanel.tsx
└─ README.md                   # 이 파일
```

## 핵심 파일

### 타입 정의
- `types/strategy-draft.ts`: Draft State 타입 정의

### 유틸리티
- `lib/strategy-draft-utils.ts`: Draft 생성 및 조작 함수
- `lib/draft-validation.ts`: PRD/TRD 규칙 검증
- `lib/draft-to-json.ts`: Draft → Strategy JSON 변환

## 접근 방법

1. **웹 UI**: `/strategies` 페이지에서 "전략 빌더 (UI)" 버튼 클릭
2. **직접 URL**: `http://localhost:3000/strategies/builder`

## 개발 가이드

### Draft State
UI 전용 상태로, 사용자 친화적 구조를 가집니다.

```typescript
interface StrategyDraft {
  name: string;
  description: string;
  indicators: IndicatorDraft[];
  entry: EntryDraft;
  stopLoss: StopLossDraft;
  reverse: ReverseDraft;
  hook: HookDraft;
}
```

### Strategy JSON
백엔드 전송용으로, Schema v1.0을 준수합니다.

```typescript
interface StrategyJSON {
  schema_version: '1.0';
  meta: { name: string; description: string };
  indicators: IndicatorJSON[];
  entry: EntryJSON;
  stop_loss: StopLossJSON;
  reverse: ReverseJSON;
  hook: HookJSON;
}
```

### Validation 규칙

1. 전략 이름 필수
2. 지표 ID 중복 불가
3. 진입 조건 최소 1개 (롱 또는 숏)
4. 조건 좌변/우변 필수
5. cross 연산자는 양쪽 모두 지표
6. 손절 방식 필수
7. ATR 기반 SL 시 ATR 지표 존재 확인

## 참조 문서

- `AlgoForge_Strategy_Builder_Implementation_Guide_v1.0.md`
- `AlgoForge_PRD_v1.0.md`
- `AlgoForge_TRD_v1.0.md`

## 주의 사항

### 절대 금지
1. ❌ Strategy JSON Schema v1.0 구조 변경
2. ❌ PRD/TRD 규칙 단순화
3. ❌ Draft 자동 보정
4. ❌ 비결정적 요소 추가

### 필수 준수
1. ✅ Draft State는 UI 전용
2. ✅ Validation 실패 시 JSON 생성 금지
3. ✅ 동일 Draft → 동일 strategy_hash
4. ✅ JSON Preview는 Read-only

