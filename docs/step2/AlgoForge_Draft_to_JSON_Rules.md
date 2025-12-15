# Draft → Strategy JSON 변환 규칙

## 목적
- UI Draft 상태를 결정적 JSON으로 변환
- PRD/TRD 규칙 준수 보장

---

## 변환 순서

1. Meta
- UI 이름/설명 → meta

2. Indicators
- indicatorsDraft → indicators[]
- id 자동 생성 또는 고정

3. Entry
- ConditionRow → { left, op, right }
- AND 배열로 정렬

4. Stop Loss
- Draft 선택값 → stop_loss 객체

5. Reverse
- 기본: use_entry_opposite=true

6. Hook
- 기본: enabled=false

---

## Canonicalization
- meta 제외
- key 정렬
- whitespace 제거
- 동일 Draft → 동일 strategy_hash

---

## 실패 조건
- 필수 항목 누락 시 JSON 생성 불가
- Validation 실패 시 저장 불가
