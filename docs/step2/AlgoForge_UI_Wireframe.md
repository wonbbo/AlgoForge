# 전략 빌더 UI 와이어프레임 (텍스트 기반)

## 목적
- Strategy JSON 구조는 유지
- 사용자는 JSON을 직접 작성하지 않음
- UI를 통해 단계적으로 전략을 ‘조립’

---

## 전체 화면 구성
[Header]
- 전략 이름 입력
- 저장 / 실행 버튼

[Main]
- Step Wizard (좌측)
- Preview 패널 (우측)

---

## Step 1. 지표 선택 (Indicator Wizard)
- 카테고리별 카드
  - Trend: EMA, SMA
  - Momentum: RSI
  - Volatility: ATR
- 카드 클릭 시 기본 파라미터로 추가
- 파라미터는 최소 입력만 허용

출력:
- indicators[] draft 생성

---

## Step 2. 진입 조건 (Condition Builder)
- Long / Short 탭
- 조건 리스트 (AND)
- 조건 1줄 = 문장형 UI
  - [좌] 지표 선택
  - [중] 연산자 선택
  - [우] 지표 또는 숫자

출력:
- entry.long.and[]
- entry.short.and[]

---

## Step 3. 손절 방식
- Radio: 고정 % / ATR
- 입력 필드 최소화

출력:
- stop_loss

---

## Advanced
- Reverse Signal: 기본값 use_entry_opposite
- Hook: OFF 기본

---

## JSON Preview
- Read-only
- Copy / Download 지원
