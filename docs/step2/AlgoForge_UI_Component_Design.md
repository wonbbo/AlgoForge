# 전략 빌더 UI 컴포넌트 & 상태 설계 (ShadCN 기준)

## 핵심 상태 구조 (Draft)
- StrategyDraft
  - indicatorsDraft[]
  - entryDraft.long.conditions[]
  - entryDraft.short.conditions[]
  - stopLossDraft
  - reverseDraft
  - hookDraft

---

## 주요 컴포넌트
- StrategyBuilderPage
- StepWizard
- IndicatorSelector
- ConditionRow
- StopLossSelector
- JsonPreviewPanel

---

## 상태 흐름
User Input
 → Draft State Update
 → Validation
 → JSON Export (Schema v1.0)

---

## Validation 규칙
- indicator id 중복 금지
- entry 조건 최소 1개
- cross 연산자 제약
- stop_loss 필수

---

## UX 규칙
- 오류는 즉시 표시
- JSON은 자동 생성
- 고급 기능은 숨김
