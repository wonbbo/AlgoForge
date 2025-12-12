# AlgoForge 전략 빌더 UI 구현용 AI 프롬프트

당신은 시니어 프론트엔드/풀스택 엔지니어입니다.
아래 문서들을 모두 읽고, **전략 JSON 구조를 변경하지 않고**
사용자 친화적인 전략 빌더 UI를 구현하세요.

---

## 1. 절대 전제 (가장 중요)
- Strategy JSON Schema v1.0은 **절대 변경 금지**
- PRD / TRD / ADR 규칙은 모두 상위 규칙
- UI는 Draft State를 관리하고, 최종 산출물은 JSON

---

## 2. 반드시 참고할 문서
1. AlgoForge_PRD_v1.0L.md
2. AlgoForge_TRD_v1.0.md
3. AlgoForge_ADR_v1.0.md
4. AlgoForge_UI_Wireframe.md
5. AlgoForge_UI_Component_Design.md
6. AlgoForge_Draft_to_JSON_Rules.md

---

## 3. 구현 목표
- JSON을 모르는 사용자도 전략을 만들 수 있어야 함
- 입력은 단계별(Wizard)로 제공
- 모든 입력은 Draft 상태로 관리
- 저장/실행 시 Draft → Strategy JSON으로 변환

---

## 4. UI 구현 요구사항

### 4.1 기술 스택
- Next.js (App Router)
- ShadCN UI
- TailwindCSS
- TypeScript

### 4.2 화면 구성
- 전략 빌더 페이지
- Step Wizard:
  1. Indicator 선택
  2. Entry 조건 구성
  3. Stop Loss 선택
- Advanced:
  - Reverse (기본 use_entry_opposite)
  - Hook (기본 OFF)
- JSON Preview (read-only)

---

## 5. Draft State 규칙
- Draft는 UI 전용 상태
- JSON은 Draft에서만 생성
- Validation 실패 시 JSON 생성 금지

---

## 6. Validation 필수 규칙
- indicator id 중복 불가
- entry 조건 최소 1개 필요
- cross 연산자 제약 준수
- stop_loss 필수

---

## 7. 변환 규칙
- Draft → JSON 변환은
  AlgoForge_Draft_to_JSON_Rules.md를 그대로 따를 것
- Canonicalization 보장

---

## 8. 산출물 요구
- 전략 빌더 UI 코드
- Draft 타입 정의
- JSON 생성 함수
- 주요 컴포넌트 코드 예시

---

## 9. 금지 사항
- JSON 구조 단순화
- 규칙 UI에서 삭제
- PRD/TRD에 없는 자동 보정 로직 추가

---

## 10. 성공 기준
- UI로 만든 전략 JSON이
  기존 수동 작성 JSON과 100% 호환
- 동일 Draft → 동일 strategy_hash 생성 가능

이 지침을 어기면 구현은 실패로 간주됩니다.
