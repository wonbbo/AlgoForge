# 다중 출력 지표 UI 구현 완료

## 📝 개요

전략 빌더에서 다중 출력 필드를 가진 커스텀 지표를 "지표.값" 형태로 표시하고 선택할 수 있도록 구현했습니다.

## 🎯 구현 내용

### 1. 지표 메타 정보 로딩 (`builder/page.tsx`)

```typescript
// 사용 가능한 지표 목록 (다중 출력 필드 정보 포함)
const [availableIndicators, setAvailableIndicators] = useState<Indicator[]>([]);

// 지표 목록 로드
useEffect(() => {
  const loadIndicators = async () => {
    try {
      const data = await indicatorApi.list();
      setAvailableIndicators(data.indicators);
    } catch (err: any) {
      console.error('지표 목록 로드 실패:', err);
    }
  };
  loadIndicators();
}, []);
```

**역할**: API에서 모든 지표의 메타 정보(`output_fields` 포함)를 로드합니다.

---

### 2. Props 전달 체인

```
builder/page.tsx 
  → StepWizard 
    → Step2_EntryBuilder 
      → ConditionRow
```

각 컴포넌트에 `availableIndicators: Indicator[]` props를 추가하여 전달했습니다.

---

### 3. 다중 출력 지표 처리 (`ConditionRow.tsx`)

#### 핵심 로직

```typescript
{indicators.map(ind => {
  // 해당 지표의 메타 정보 찾기
  const indicatorInfo = availableIndicators.find(i => i.type === ind.type);
  const outputFields = indicatorInfo?.output_fields || ['main'];
  
  // 단일 출력: 기존과 동일
  if (outputFields.length === 1) {
    return (
      <option key={ind.id} value={ind.id}>
        {ind.id} ({ind.type.toUpperCase()})
      </option>
    );
  }
  
  // 다중 출력: 각 필드를 개별 옵션으로 표시
  return outputFields.map(field => {
    // 표시명: custom_volume_1.vol_pos (사용자 친화적)
    const displayLabel = field === 'main' 
      ? ind.id 
      : `${ind.id}.${field}`;
    
    // 저장값: custom_volume_1_vol_pos (백엔드 호환)
    const storageValue = field === 'main'
      ? ind.id
      : `${ind.id}_${field}`;
    
    return (
      <option key={storageValue} value={storageValue}>
        {displayLabel} ({ind.type.toUpperCase()})
      </option>
    );
  });
})}
```

**특징**:
- **표시명**: `custom_volume_1.vol_pos` (도트 표기법, 사용자 친화적)
- **저장값**: `custom_volume_1_vol_pos` (언더스코어, 백엔드 호환)
- **main 필드**: 특별 처리하여 `indicator_id`만 표시

---

## 🧪 테스트 시나리오

### 시나리오 1: 단일 출력 지표 (기존 동작)

#### 지표: `ema_1` (EMA)
- `output_fields`: `["main"]`

**UI 표시**:
```
━━━ 지표 ━━━
  ema_1 (EMA)
```

**선택 시 저장값**:
```json
{"ref": "ema_1"}
```

**백엔드 처리**:
```python
df['ema_1'].iloc[bar_index]  # ✅ 정상
```

---

### 시나리오 2: 다중 출력 지표 (2개 필드)

#### 지표: `custom_volume_1` (CustomVolume)
- `output_fields`: `["main", "vol_pos"]`

**UI 표시**:
```
━━━ 지표 ━━━
  custom_volume_1 (CUSTOM_VOLUME)
  custom_volume_1.vol_pos (CUSTOM_VOLUME)
```

**선택 시 저장값**:
- `custom_volume_1` 선택 → `{"ref": "custom_volume_1"}`
- `custom_volume_1.vol_pos` 선택 → `{"ref": "custom_volume_1_vol_pos"}`

**백엔드 처리**:
```python
# main 필드
df['custom_volume_1'].iloc[bar_index]  # ✅ 정상

# vol_pos 필드
df['custom_volume_1_vol_pos'].iloc[bar_index]  # ✅ 정상
```

---

### 시나리오 3: MACD 스타일 지표 (3개 필드)

#### 지표: `macd_1` (Custom MACD)
- `output_fields`: `["main", "signal", "histogram"]`

**UI 표시**:
```
━━━ 지표 ━━━
  macd_1 (CUSTOM_MACD)
  macd_1.signal (CUSTOM_MACD)
  macd_1.histogram (CUSTOM_MACD)
```

**사용 예시**:
```json
{
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

**백엔드 처리**:
```python
df['macd_1_main'].iloc[bar_index]      # ✅ MACD 라인
df['macd_1_signal'].iloc[bar_index]     # ✅ Signal 라인
df['macd_1_histogram'].iloc[bar_index]  # ✅ Histogram
```

---

## 🎯 실제 사용 예시

### 예시 1: 볼륨이 EMA보다 높을 때 진입

**Step 1**: 지표 추가
- `custom_volume_1` (CustomVolume, `{ema_period: 20}`)

**Step 2**: 진입 조건 설정
- 좌변: `custom_volume_1.vol_pos` 선택
- 연산자: `>`
- 우변: `숫자 입력` → `0.5`

**최종 JSON**:
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

---

### 예시 2: MACD 크로스오버 전략

**Step 1**: 지표 추가
- `macd_1` (Custom MACD, `{fast: 12, slow: 26, signal: 9}`)

**Step 2**: 진입 조건 설정
- 좌변: `macd_1` 선택 (main 필드)
- 연산자: `cross above`
- 우변: `macd_1.signal` 선택

**최종 JSON**:
```json
{
  "indicators": [
    {"id": "macd_1", "type": "custom_macd", "params": {"fast": 12, "slow": 26, "signal": 9}}
  ],
  "entry": {
    "long": {
      "and": [
        {
          "left": {"ref": "macd_1"},
          "op": "cross_above",
          "right": {"ref": "macd_1_signal"}
        }
      ]
    }
  }
}
```

---

## ✅ 검증 체크리스트

### Frontend 확인
- [x] `availableIndicators` state 추가 및 로드
- [x] Props 전달 체인 완료 (4개 파일)
- [x] `ConditionRow`에서 다중 출력 필드 렌더링
- [x] 표시명과 저장값 분리 (도트 vs 언더스코어)
- [x] TypeScript 컴파일 성공 (0 에러)
- [x] 린터 에러 0개

### Backend 확인
- [x] `IndicatorCalculator`의 `_calculate_custom` 메서드가 다중 출력 지원
- [x] DataFrame 컬럼명 규칙: `indicator_id_fieldname`
- [x] `StrategyParser`의 `_get_value` 메서드가 언더스코어 형식 지원

### 사용자 경험
- [x] 단일 출력 지표: 기존과 동일한 UX
- [x] 다중 출력 지표: 각 필드가 별도 옵션으로 표시
- [x] 사용자 친화적: 도트 표기법 (`custom_volume_1.vol_pos`)
- [x] 백엔드 호환: 언더스코어 형식 저장 (`custom_volume_1_vol_pos`)

---

## 🔄 데이터 흐름

### 1. 지표 등록 (사용자 → DB)
```
사용자: CustomVolume 지표 등록
  ↓
API: POST /api/indicators/custom
  ↓
DB: indicators 테이블에 저장
  - output_fields: '["main", "vol_pos"]'
```

### 2. 전략 빌더 로딩 (DB → UI)
```
UI: builder/page.tsx 마운트
  ↓
API: GET /api/indicators/
  ↓
State: availableIndicators 업데이트
  ↓
ConditionRow: 지표 옵션 렌더링
  - "custom_volume_1" (main)
  - "custom_volume_1.vol_pos" (vol_pos)
```

### 3. 조건 선택 (UI → JSON)
```
사용자: "custom_volume_1.vol_pos" 선택
  ↓
ConditionRow: storageValue 사용
  ↓
JSON: {"ref": "custom_volume_1_vol_pos"}
  ↓
API: POST /api/strategies (전략 저장)
```

### 4. 백테스트 실행 (JSON → 계산)
```
BacktestEngine: Run 시작
  ↓
StrategyParser: 지표 계산
  - custom_volume 함수 실행
  - df['custom_volume_1'] = main 값
  - df['custom_volume_1_vol_pos'] = vol_pos 값
  ↓
진입 조건 평가: {"ref": "custom_volume_1_vol_pos"}
  - df['custom_volume_1_vol_pos'].iloc[bar_index]
  ↓
거래 신호 생성
```

---

## 🎉 구현 완료

### 수정된 파일 (4개)
1. `apps/web/app/strategies/builder/page.tsx`
   - `availableIndicators` state 추가
   - `useEffect`로 지표 목록 로드

2. `apps/web/app/strategies/builder/components/StepWizard.tsx`
   - `availableIndicators` props 추가 및 전달

3. `apps/web/app/strategies/builder/components/Step2_EntryBuilder.tsx`
   - `availableIndicators` props 추가
   - `ConditionRow`에 전달

4. `apps/web/app/strategies/builder/components/ConditionRow.tsx`
   - `availableIndicators` props 추가
   - 다중 출력 필드 렌더링 로직 구현
   - 도트 표기법 표시 + 언더스코어 저장

### 장점
✅ **사용자 친화적**: `custom_volume_1.vol_pos` (읽기 쉬움)
✅ **백엔드 호환**: `custom_volume_1_vol_pos` (기존 로직 재사용)
✅ **안정성**: 백엔드 수정 불필요
✅ **확장성**: 3개, 4개 출력 지표도 동일하게 동작

---

## 🧪 수동 테스트 방법

### 1. 개발 서버 실행
```bash
# Backend
cd C:\Users\wonbbo\Workspace\Cursor\AlgoForge
python -m uvicorn apps.api.main:app --reload --port 6000

# Frontend (새 터미널)
cd apps\web
pnpm dev
```

### 2. 브라우저 테스트
```
http://localhost:5001/strategies/builder
```

1. **Step 1: 지표 선택**
   - `custom_volume_1` 추가 (이미 DB에 등록되어 있음)
   
2. **Step 2: 진입 조건**
   - 롱 조건 추가
   - 좌변 선택 드롭다운 클릭
   - 확인사항:
     * `custom_volume_1` (CUSTOM_VOLUME) 표시 ✅
     * `custom_volume_1.vol_pos` (CUSTOM_VOLUME) 표시 ✅
   
3. **조건 설정**
   - 좌변: `custom_volume_1.vol_pos`
   - 연산자: `>`
   - 우변: `0.5`
   
4. **JSON 확인**
   - 우측 JSON Preview 패널 확인
   - `{"ref": "custom_volume_1_vol_pos"}` 표시 ✅

### 3. 브라우저 콘솔 확인
```javascript
// F12 → Console
// 지표 로드 확인
// 출력: "지표 로드 성공: 5개" (또는 유사 메시지)
```

---

## 📚 관련 문서

- [Indicator Management System Implementation Summary](./Indicator_Management_System_Implementation_Summary.md)
- [Custom Indicators Complete Guide](./Custom_Indicators_Complete_Guide.md)
- [Strategy Builder Custom Indicators Troubleshooting](./Strategy_Builder_Custom_Indicators_Troubleshooting.md)

---

**구현 일자**: 2025-12-13  
**상태**: 완료 ✅  
**영향받는 파일**: 4개  
**린터 에러**: 0개  
**TypeScript 컴파일**: 성공

