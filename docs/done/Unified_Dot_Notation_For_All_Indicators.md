# 모든 지표에 일관된 도트 표기법 적용

## 📝 개요

전략 빌더의 진입 조건(Step 2)에서 **모든 지표**(내장+커스텀)에 일관된 "지표.값" 형태를 적용했습니다.

## 🎯 변경 사항

### 이전 (불일치)

```
━━━ 지표 ━━━
  ema_1 (EMA)                         ← 도트 없음
  rsi_1 (RSI)                         ← 도트 없음
  custom_volume_1 (CUSTOM_VOLUME)     ← 도트 없음 (main)
  custom_volume_1.vol_pos (CUSTOM_VOLUME)  ← 도트 있음 (필드명)
```

**문제점**: 단일/다중 출력 지표의 표기법이 다르고, 지표명이 중복 표시됨

---

### 이후 (일관됨) ✅

```
━━━ 지표 ━━━
  ema_1.ema                           ← 지표.지표타입
  rsi_1.rsi                           ← 지표.지표타입
  custom_volume_1.custom_volume       ← 지표.지표타입 (main)
  custom_volume_1.vol_pos             ← 지표.필드명
```

**장점**:
- ✅ 모든 지표가 "지표.값" 형태로 통일
- ✅ 어떤 값을 참조하는지 명확
- ✅ 중복 표시 제거 (지표명 한 번만 표시)

---

## 🔧 구현 로직

### ConditionRow.tsx

```typescript
{indicators.map(ind => {
  // 지표 메타 정보 찾기
  const indicatorInfo = availableIndicators.find(i => i.type === ind.type);
  const outputFields = indicatorInfo?.output_fields || ['main'];
  
  // 모든 지표를 "지표.값" 형태로 표시
  return outputFields.map(field => {
    // 표시명 생성
    let displayLabel: string;
    if (field === 'main') {
      // main 필드는 지표 타입명 사용: ema_1.ema
      displayLabel = `${ind.id}.${ind.type}`;
    } else {
      // 나머지는 필드명 사용: custom_volume_1.vol_pos
      displayLabel = `${ind.id}.${field}`;
    }
    
    // 저장값: 백엔드 호환 (언더스코어)
    const storageValue = field === 'main'
      ? ind.id
      : `${ind.id}_${field}`;
    
    return (
      <option key={storageValue} value={storageValue}>
        {displayLabel}
      </option>
    );
  });
})}
```

---

## 📊 예시

### 1. 단일 출력 내장 지표 (EMA)

**지표 추가**: `ema_1` (EMA, period: 20)

**UI 표시**:
```
ema_1.ema
```

**선택 시 저장**:
```json
{"ref": "ema_1"}
```

**백엔드 처리**:
```python
df['ema_1'].iloc[bar_index]  # ✅
```

---

### 2. 다중 출력 커스텀 지표 (CustomVolume)

**지표 추가**: `custom_volume_1` (CustomVolume, ema_period: 20)
- `output_fields`: `["main", "vol_pos"]`

**UI 표시**:
```
custom_volume_1.custom_volume   ← main 필드
custom_volume_1.vol_pos         ← vol_pos 필드
```

**선택 시 저장**:
- `custom_volume_1.custom_volume` → `{"ref": "custom_volume_1"}`
- `custom_volume_1.vol_pos` → `{"ref": "custom_volume_1_vol_pos"}`

**백엔드 처리**:
```python
df['custom_volume_1'].iloc[bar_index]          # ✅ main
df['custom_volume_1_vol_pos'].iloc[bar_index]  # ✅ vol_pos
```

---

### 3. MACD 스타일 지표

**지표 추가**: `macd_1` (Custom MACD)
- `output_fields`: `["main", "signal", "histogram"]`

**UI 표시**:
```
macd_1.custom_macd      ← main 필드
macd_1.signal           ← signal 필드
macd_1.histogram        ← histogram 필드
```

**진입 조건 예시**:
```
좌변: macd_1.custom_macd
연산자: cross above
우변: macd_1.signal
```

**최종 JSON**:
```json
{
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

## 🎨 UI 개선 효과

### Before (이전)

```
━━━ 지표 ━━━
  ema_1 (EMA)
  ema_2 (EMA)
  rsi_1 (RSI)
  custom_volume_1 (CUSTOM_VOLUME)
  custom_volume_1.vol_pos (CUSTOM_VOLUME)
```

**문제점**:
- 같은 지표명이 여러 번 표시 (혼란)
- 표기법 불일치 (도트 있음/없음)
- 지표 타입 중복 표시

---

### After (이후)

```
━━━ 지표 ━━━
  ema_1.ema
  ema_2.ema
  rsi_1.rsi
  custom_volume_1.custom_volume
  custom_volume_1.vol_pos
```

**장점**:
- ✅ 일관된 표기법 (모두 도트)
- ✅ 간결한 표시 (지표명 중복 제거)
- ✅ 명확한 의미 (어떤 값인지 바로 알 수 있음)

---

## 🔄 데이터 흐름

### 1. 내장 지표 (EMA)

```
UI: "ema_1.ema" 선택
  ↓
JSON: {"ref": "ema_1"}
  ↓
Backend: df['ema_1'].iloc[bar_index]
  ↓
결과: 20봉 EMA 값
```

---

### 2. 커스텀 지표 - main 필드

```
UI: "custom_volume_1.custom_volume" 선택
  ↓
JSON: {"ref": "custom_volume_1"}
  ↓
Backend: df['custom_volume_1'].iloc[bar_index]
  ↓
결과: 볼륨 EMA 값
```

---

### 3. 커스텀 지표 - 추가 필드

```
UI: "custom_volume_1.vol_pos" 선택
  ↓
JSON: {"ref": "custom_volume_1_vol_pos"}
  ↓
Backend: df['custom_volume_1_vol_pos'].iloc[bar_index]
  ↓
결과: 볼륨 위치 값 (1.0 or 0.0)
```

---

## ✅ 검증 체크리스트

### UI 확인
- [x] 모든 지표가 "지표.값" 형태로 표시
- [x] 내장 지표: `ema_1.ema`, `rsi_1.rsi`
- [x] 커스텀 단일: `my_indicator_1.my_indicator`
- [x] 커스텀 다중: `custom_volume_1.custom_volume`, `custom_volume_1.vol_pos`
- [x] 지표 타입 중복 표시 제거

### 저장값 확인
- [x] main 필드: `indicator_id` (언더스코어 없음)
- [x] 추가 필드: `indicator_id_fieldname` (언더스코어)
- [x] 백엔드 호환성 유지

### 린트 및 컴파일
- [x] TypeScript 컴파일 성공
- [x] Lint 에러 0개

---

## 📚 관련 규칙

### 표시명 규칙

| 필드 타입 | 표시명 형식 | 예시 |
|---------|----------|-----|
| main (내장) | `{id}.{type}` | `ema_1.ema` |
| main (커스텀) | `{id}.{type}` | `custom_volume_1.custom_volume` |
| 추가 필드 | `{id}.{field}` | `custom_volume_1.vol_pos` |

### 저장값 규칙

| 필드 타입 | 저장값 형식 | 백엔드 컬럼명 |
|---------|----------|------------|
| main | `{id}` | `ema_1` |
| 추가 필드 | `{id}_{field}` | `custom_volume_1_vol_pos` |

---

## 🎉 요약

### 변경 내용
- ✅ 모든 지표에 일관된 도트 표기법 적용
- ✅ main 필드는 지표 타입명 사용
- ✅ 추가 필드는 필드명 사용
- ✅ 지표명 중복 표시 제거

### 사용자 경험 개선
- ✅ 일관성 (모든 지표가 동일한 형식)
- ✅ 명확성 (어떤 값인지 바로 이해)
- ✅ 간결성 (불필요한 정보 제거)

### 기술적 장점
- ✅ 백엔드 수정 불필요
- ✅ 하위 호환성 유지
- ✅ 확장성 (새로운 지표도 자동 적용)

---

**수정 일자**: 2025-12-13  
**수정 파일**: 1개 (`ConditionRow.tsx`)  
**영향 범위**: 전략 빌더 Step 2 (진입 조건)  
**상태**: 완료 ✅

