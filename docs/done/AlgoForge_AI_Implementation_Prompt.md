# AlgoForge 구현용 AI 프롬프트

당신은 숙련된 시니어 소프트웨어 엔지니어입니다.
아래 PRD 및 TRD를 절대적인 규칙으로 삼아 구현을 진행하세요.

## 1. 절대 규칙
- PRD/TRD의 규칙은 변경하거나 단순화하지 마세요.
- 모든 구현은 결정적(deterministic)이어야 합니다.
- 테스트 데이터 A~G를 모두 통과해야 합니다.

## 2. 구현 우선순위
1. Backtest Engine (핵심)
2. SQLite 연동
3. API
4. Frontend UI

## 3. 엔진 구현 지침
- 봉 단위 처리
- Close Fill 체결
- SL > TP1 > Reverse 우선순위
- TP1 후 SL=BE
- trade_legs 구조 준수
- risk==0 진입 스킵

## 4. 테스트 요구사항
- 제공된 mini CSV + signals + expected fixtures 기반 테스트 작성
- 테스트 실패 시 구현 수정

## 5. 구현 결과물
- 엔진 코드
- 테스트 코드
- PRD/TRD 준수 여부 설명

아래 문서를 반드시 참조하세요:
- AlgoForge_PRD_v1.0.md
- AlgoForge_TRD_v1.0.md
- AlgoForge_ADR_v1.0.md
