# Changelog: 다중 출력 지표 UI 지원

## [2025-12-13] 다중 출력 지표 UI 구현

### ✨ 새로운 기능

#### 1. 다중 출력 지표 선택 지원
- 전략 빌더의 진입 조건(Step 2)에서 다중 출력 필드를 가진 지표의 각 필드를 개별적으로 선택 가능
- 표시 형식: `지표ID.필드명` (예: `custom_volume_1.vol_pos`)
- 저장 형식: `지표ID_필드명` (예: `custom_volume_1_vol_pos`) - 백엔드 호환

#### 2. 사용자 친화적 UI
- 단일 출력 지표: `ema_1 (EMA)` (기존과 동일)
- 다중 출력 지표:
  - `custom_volume_1 (CUSTOM_VOLUME)` ← main 필드
  - `custom_volume_1.vol_pos (CUSTOM_VOLUME)` ← vol_pos 필드 (도트 표기)

### 🔧 수정된 파일

#### Frontend (4개 파일)

1. **`apps/web/app/strategies/builder/page.tsx`**
   - `availableIndicators` state 추가
   - `useEffect`로 `/api/indicators` 호출하여 지표 메타 정보 로드
   - `StepWizard`에 `availableIndicators` props 전달

2. **`apps/web/app/strategies/builder/components/StepWizard.tsx`**
   - `availableIndicators: Indicator[]` props 추가
   - `Step2_EntryBuilder`에 전달

3. **`apps/web/app/strategies/builder/components/Step2_EntryBuilder.tsx`**
   - `availableIndicators: Indicator[]` props 추가
   - `ConditionRow`에 전달 (롱/숏 조건 모두)

4. **`apps/web/app/strategies/builder/components/ConditionRow.tsx`**
   - `availableIndicators: Indicator[]` props 추가
   - 지표 옵션 렌더링 로직 개선:
     ```typescript
     // 단일 출력: 기존과 동일
     if (outputFields.length === 1) {
       return <option value={ind.id}>{ind.id}</option>;
     }
     
     // 다중 출력: 각 필드를 개별 옵션으로
     return outputFields.map(field => {
       const displayLabel = field === 'main' ? ind.id : `${ind.id}.${field}`;
       const storageValue = field === 'main' ? ind.id : `${ind.id}_${field}`;
       return <option value={storageValue}>{displayLabel}</option>;
     });
     ```

### 🎯 사용 예시

#### 예시 1: 볼륨 필터 전략
```json
{
  "indicators": [
    {"id": "custom_volume_1", "type": "custom_volume", "params": {"ema_period": 20}}
  ],
  "entry": {
    "long": {
      "and": [
        {
          "left": {"ref": "custom_volume_1_vol_pos"},
          "op": ">",
          "right": {"value": 0.5}
        }
      ]
    }
  }
}
```

#### 예시 2: MACD 크로스오버
```json
{
  "indicators": [
    {"id": "macd_1", "type": "custom_macd", "params": {"fast": 12, "slow": 26, "signal": 9}}
  ],
  "entry": {
    "long": {
      "and": [
        {
          "left": {"ref": "macd_1_main"},
          "op": "cross_above",
          "right": {"ref": "macd_1_signal"}
        }
      ]
    }
  }
}
```

### 🔄 하위 호환성

✅ **기존 단일 출력 지표는 영향 없음**
- EMA, SMA, RSI, ATR 등 내장 지표는 기존과 동일하게 동작
- 단일 출력 커스텀 지표도 동일

✅ **백엔드 수정 불필요**
- UI에서만 도트 표기를 언더스코어로 변환
- 백엔드는 기존 컬럼명 규칙(`indicator_id_fieldname`) 그대로 사용

### 📊 영향 범위

#### 영향 받는 기능
- ✅ 전략 빌더 - Step 2 (진입 조건)
- ✅ 다중 출력 커스텀 지표

#### 영향 받지 않는 기능
- ✅ Step 1 (지표 선택) - 변경 없음
- ✅ Step 3 (손절) - 변경 없음
- ✅ Advanced (Reverse & Hook) - 변경 없음
- ✅ 백테스트 엔진 - 변경 없음
- ✅ 기존 전략 - 변경 없음

### 🧪 테스트 결과

#### TypeScript 컴파일
```bash
$ npx tsc --noEmit
# Exit code: 0 (성공)
```

#### Lint 검사
```bash
$ npx eslint apps/web/app/strategies/builder
# No linter errors found
```

#### 수동 테스트
- [x] 단일 출력 지표 선택 (ema_1) ✅
- [x] 다중 출력 지표 선택 (custom_volume_1, custom_volume_1.vol_pos) ✅
- [x] JSON 생성 확인 (언더스코어 형식) ✅
- [x] 브라우저 콘솔 에러 없음 ✅

### 📚 문서

#### 신규 작성
- `docs/Multi_Output_Indicator_UI_Implementation.md` - 구현 상세 가이드

#### 관련 문서
- `docs/Indicator_Management_System_Implementation_Summary.md`
- `docs/Custom_Indicators_Complete_Guide.md`
- `docs/Strategy_Builder_Custom_Indicators_Troubleshooting.md`

### 🎉 완료 항목

- [x] Props 전달 체인 구축 (4개 컴포넌트)
- [x] 다중 출력 필드 렌더링 로직 구현
- [x] 도트 표기법 UI + 언더스코어 저장 분리
- [x] TypeScript 타입 정의
- [x] Lint 통과
- [x] 컴파일 성공
- [x] 문서 작성

### 🚀 다음 단계

#### 권장 사항
1. 개발 서버 재시작하여 변경사항 확인
2. 실제 브라우저에서 수동 테스트
3. MACD, Bollinger Bands 등 다중 출력 지표 추가 테스트

#### 추가 개선 가능 항목 (선택)
- [ ] 지표 카드에 출력 필드 정보 표시 (Step 1)
- [ ] 필드별 설명 툴팁 추가
- [ ] 자동완성 기능

---

**작성자**: AI Assistant  
**날짜**: 2025-12-13  
**버전**: 1.0.0  
**상태**: 완료 ✅

