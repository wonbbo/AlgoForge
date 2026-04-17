# Strategy Builder: 사용자 지표(가격 레벨) 기반 손절 설계

## 목적
- 전략 빌더의 **Step 3: 손절 방식 선택**에 기존
  - 고정 퍼센트(`fixed_percent`)
  - ATR 기반(`atr_based`)
  에 더해,
- **사용자(내장/커스텀) 지표를 손절가(가격 레벨)로 사용하는 방식**을 추가한다.

핵심 사용 사례:
- 커스텀 지표 `sma_channel`이 `high_sma_20`, `low_sma_20` 같은 **채널(밴드) 가격 레벨**을 출력할 때
  - LONG이면 `low_sma_20`을 손절가로 사용
  - SHORT이면 `high_sma_20`을 손절가로 사용

## 배경(현재 구현 요약)
- 프론트 Draft 타입: `apps/web/types/strategy-draft.ts`의 `StopLossDraft`는 현재 `fixed_percent`, `atr_based`만 지원.
- 프론트 JSON 변환: `apps/web/lib/draft-to-json.ts`에서 `stop_loss`를 전략 JSON으로 변환.
  - `StopLossJSON`에는 이미 `function_based`가 정의되어 있으나, validation 주석상 **MVP에서는 미지원(v2 예정)**.
- 엔진 손절 계산: `engine/utils/strategy_parser.py`의 `_calculate_stop_loss()`가 현재 `fixed_percent`, `fixed_points`, `atr_based` 처리.
- 커스텀 지표 다중 출력 저장 규칙:
  - `engine/utils/indicators.py`에서 커스텀 지표가 `{'main': ..., 'signal': ...}` 같은 dict를 반환하면
    - `main`은 `indicator_id` 컬럼에 저장
    - 나머지는 `indicator_id_<field>` 컬럼에 저장
- 지표 참조(dot notation) 지원:
  - `engine/utils/strategy_parser.py`는 `indicatorId.field`를 `indicatorId_field`로 변환해 컬럼 접근 가능.

## 설계 결정
### 1) 손절 의미
- 새 손절 방식은 **지표 값 자체가 손절가(가격 레벨)**를 의미한다.
  - (ATR처럼 거리/퍼센트 해석이 아니라) “현재 봉에서 계산된 특정 레벨”을 SL 가격으로 사용한다.

### 2) LONG/SHORT 별 참조 분리(확정)
- 손절 설정에 **롱과 숏의 지표 참조를 각각 저장**한다.
  - 이유: 다중 출력 지표에서 롱/숏이 서로 다른 필드를 쓸 수 있어야 하며,
    참조 문자열을 그대로 엔진이 해석할 수 있어 구조가 단순하다.

### 3) 실패 정책(확정)
- 선택한 손절 지표 값으로 **유효한 손절가를 만들 수 없으면(컬럼 없음/NaN/비정상/방향과 모순)**:
  - **그 봉의 진입을 스킵**
  - **warning을 run_artifacts에 기록**
- ATR 기반 손절에서 `atr_value <= 0`이면 진입 스킵하는 정책과 동일한 철학을 따른다.

## Strategy JSON 스키마 확장안
> 현재 프론트 주석에 “Schema v1.0 절대 변경 불가”가 있으나, 현실적으로 기능 추가를 위해 `stop_loss`의 union을 확장하는 형태로 진행한다.
> (기존 전략 호환성을 깨지 않도록 **새 타입 추가**만 수행)

### 새 타입: `indicator_level`
```json
{
  "stop_loss": {
    "type": "indicator_level",
    "long_ref": "sma_ch_1.low_sma_20",
    "short_ref": "sma_ch_1.high_sma_20"
  }
}
```

#### 참조 문자열 규칙
- **단일 출력(main)만 쓰는 경우**
  - `my_vwap` 처럼 `indicator_id`만 저장 (권장)
- **다중 출력 필드를 쓰는 경우**
  - `indicator_id.field` 형태로 저장 (예: `sma_ch_1.low_sma_20`)
- 주의: 엔진 컬럼 규칙상 `main` 출력은 `indicator_id`에 저장되므로
  - `.main`은 저장하지 않는 것을 기본으로 한다.

## 프론트(UI) 설계
### Step 3 UI
- `apps/web/app/strategies/builder/components/Step3_StopLossSelector.tsx`에 3번째 옵션 카드 추가:
  - “사용자 지표 기반(가격 레벨)”
- 입력 요소:
  - LONG 손절 참조 선택: 지표 선택 + (필요 시) 출력 필드 선택
  - SHORT 손절 참조 선택: 지표 선택 + (필요 시) 출력 필드 선택
- 다중 출력 지원:
  - 지표 메타(`output_fields`)는 API의 `Indicator` 타입(`apps/web/lib/types.ts`)에서 제공됨
  - 따라서 Step3에 `availableIndicators`(메타)와 `isLoadingIndicators`를 전달해야 함
    - 현재 Step2는 이미 이를 받고 있으므로, `StepWizard.tsx`에서 Step3에도 같은 props를 넘기는 방향이 자연스럽다.

### 기본값(UX)
- 가능한 경우 자동 추천:
  - LONG은 `low*` 포함 필드, SHORT는 `high*` 포함 필드 우선
  - 없으면 각 방향 첫 필드
- 단일 출력(= `output_fields: ["main"]`)이면 필드 선택 UI를 숨기고 ref는 `indicator_id`로 저장

## 프론트(Draft/Validation/변환) 설계
### Draft 타입
- `StopLossDraft`에 아래 변형 추가:
  - `{ type: 'indicator_level'; long_ref: string; short_ref: string }`

### Draft → JSON 변환
- `apps/web/lib/draft-to-json.ts`의 `StopLossJSON` union에 추가:
  - `{ type: 'indicator_level'; long_ref: string; short_ref: string }`
- `convertStopLoss()`에서 위 타입 처리 추가

### JSON → Draft 역변환
- `apps/web/lib/json-to-draft.ts`의 `convertStopLossToDraft()`에 `indicator_level` 처리 추가

### Validation
- `apps/web/lib/draft-validation.ts`에 `indicator_level` 검증 추가:
  - `long_ref`, `short_ref`가 빈 문자열이 아닌지
  - `ref`에서 `indicator_id` 추출(`split('.')[0]`) 후 Draft `indicators`에 존재하는지
  - (가능하면) `availableIndicators`가 접근 가능한 구조라면 `field`가 `output_fields`에 포함되는지도 검증
    - 단, 현재 validation 함수 시그니처는 `draft`만 받으므로 메타 검증은 UI 레벨에서 보조 검증으로 처리할 수 있다.

## 엔진 설계
### 손절 계산 로직 추가
- `engine/utils/strategy_parser.py`의 `_calculate_stop_loss()`에 `sl_type == "indicator_level"` 분기 추가

처리 흐름:
1. `direction == LONG`이면 `long_ref`, `SHORT`이면 `short_ref` 선택
2. ref를 컬럼명으로 변환(기존 `_parse_indicator_ref()` 재사용)
3. `indicator_calc.get_value(column, bar_index)`로 값 로드
4. 방어 로직(실패 정책 A 적용):
   - 값이 None/NaN/inf 이면 진입 스킵(None 반환)
   - 값이 0 이하(가격 레벨로 부적절)면 진입 스킵
   - LONG인데 `stop_loss >= entry_price`면 진입 스킵 (손절이 진입가 위에 있으면 리스크 0/음수 가능)
   - SHORT인데 `stop_loss <= entry_price`면 진입 스킵
   - 스킵 사유는 warning으로 기록(기존 run_artifacts 기록 방식과 통일)

## 예시(사용 사례)
### 1) SMA 채널 기반 손절
```json
{
  "schema_version": "1.0",
  "meta": { "name": "SMA Channel SL", "description": "롱은 하단, 숏은 상단" },
  "indicators": [
    {
      "id": "sma_ch_1",
      "type": "sma_channel",
      "params": { "period": 20 }
    }
  ],
  "entry": {
    "long": { "and": [ { "left": { "price": "close" }, "op": ">", "right": { "ref": "sma_ch_1.high_sma_20" } } ] },
    "short": { "and": [ { "left": { "price": "close" }, "op": "<", "right": { "ref": "sma_ch_1.low_sma_20" } } ] }
  },
  "stop_loss": {
    "type": "indicator_level",
    "long_ref": "sma_ch_1.low_sma_20",
    "short_ref": "sma_ch_1.high_sma_20"
  },
  "reverse": { "enabled": true, "mode": "use_entry_opposite" },
  "hook": { "enabled": false }
}
```

## 테스트 계획(최소)
- 프론트:
  - `apps/web/__tests__/draft-to-json.test.ts`에 `indicator_level` 변환 케이스 추가
  - `json-to-draft` 역변환 케이스 추가(필요 시)
- 엔진:
  - `indicator_level`에서 LONG/SHORT가 올바른 ref를 사용하고,
    잘못된 값일 때 진입을 스킵하도록 `_calculate_stop_loss()`가 `None`을 반환하는지 검증

## 호환성/마이그레이션
- 기존 전략(`fixed_percent`, `atr_based`)은 영향 없음.
- 저장된 JSON에 `stop_loss.type == "indicator_level"`이 들어오면
  - 구버전 UI/엔진에서는 미지원이므로, 배포 시 **프론트/엔진 동시 업데이트**가 필요.

## 추후 확장 아이디어(v2+)
- `indicator_distance`(entry ± indicator × multiplier)처럼 거리 해석 옵션 추가
- `indicator_percent`(entry × (1 ± indicator/100)) 옵션 추가
- `availableIndicators` 메타 기반으로 Step3에서 `output_fields` 유효성까지 강제 검증

---

## 구현 완료 (2026-01-11)

### 변경된 파일
1. **타입 정의**
   - `apps/web/types/strategy-draft.ts`: `StopLossDraft`에 `indicator_level` 타입 추가
   - `apps/web/lib/draft-to-json.ts`: `StopLossJSON`에 `indicator_level` 타입 추가

2. **변환 로직**
   - `apps/web/lib/draft-to-json.ts`: `convertStopLoss()`에 `indicator_level` 변환 추가
   - `apps/web/lib/json-to-draft.ts`: `convertStopLossToDraft()`에 `indicator_level` 역변환 추가

3. **검증 로직**
   - `apps/web/lib/draft-validation.ts`: `indicator_level` 검증 추가 (참조 존재 여부 확인)

4. **UI 컴포넌트**
   - `apps/web/app/strategies/builder/components/Step3_StopLossSelector.tsx`: 
     - `indicator_level` 옵션 카드 추가
     - `IndicatorRefSelector` 컴포넌트 구현 (LONG/SHORT 별 지표+필드 선택)
     - 자동 필드 추천 (low* → LONG, high* → SHORT)
   - `apps/web/app/strategies/builder/components/StepWizard.tsx`: 
     - Step3에 `availableIndicators`, `isLoadingIndicators` props 전달

5. **엔진**
   - `engine/utils/strategy_parser.py`: `_calculate_stop_loss()`에 `indicator_level` 분기 추가
     - 방향에 따라 `long_ref` 또는 `short_ref` 선택
     - 참조를 컬럼명으로 변환 (`_parse_indicator_ref()` 재사용)
     - 방어 로직: NaN/inf/0이하/방향 모순 시 진입 스킵 + warning

6. **테스트**
   - `apps/web/__tests__/draft-to-json.test.ts`: `indicator_level` 변환 테스트 2개 추가

### 테스트 결과
- 프론트 테스트: 87개 모두 통과 ✅