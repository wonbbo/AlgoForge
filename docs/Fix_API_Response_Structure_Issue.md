# API 응답 구조 불일치 문제 해결

## 📝 문제

전략 빌더에서 지표 목록을 로드할 때 다음 에러가 발생했습니다:

```javascript
지표 목록 로드 실패: TypeError: Cannot read properties of undefined (reading 'length')
    at loadIndicators (page.tsx:59:71)
```

### 원인

**API 클라이언트 vs 페이지 코드 불일치**

#### API 클라이언트 (`lib/api-client.ts`)
```typescript
export const indicatorApi = {
  list: async () => {
    const response = await fetchApi<IndicatorListResponse>(endpoint)
    return response.indicators  // ✅ 배열을 반환
  }
}
```

#### 페이지 코드 (Before)
```typescript
const data = await indicatorApi.list();
console.log('[Builder] 지표 목록 로드 완료:', data.indicators.length, '개');
//                                               ^^^^^^^^^^ ❌ undefined!
setAvailableIndicators(data.indicators);  // ❌ undefined
```

**문제**:
- `indicatorApi.list()`는 **이미 `indicators` 배열**을 반환
- 하지만 페이지에서 `data.indicators`로 다시 접근 시도
- `data`는 이미 배열이므로 `data.indicators`는 undefined
- `undefined.length` → 에러 발생!

---

## ✅ 해결 방법

### 수정된 코드

**파일**: `apps/web/app/strategies/builder/page.tsx`

```typescript
// Before (에러)
const data = await indicatorApi.list();
console.log('[Builder] 지표 목록 로드 완료:', data.indicators.length, '개');
setAvailableIndicators(data.indicators);

// After (해결)
const data = await indicatorApi.list();
// indicatorApi.list()는 이미 배열을 반환함 (response.indicators)
console.log('[Builder] 지표 목록 로드 완료:', data.length, '개');
setAvailableIndicators(data);  // ✅ 배열을 직접 사용
```

---

## 🔄 데이터 흐름

### API 응답 구조

```javascript
// Backend API Response
{
  "indicators": [
    {"indicator_id": 1, "name": "EMA", ...},
    {"indicator_id": 2, "name": "RSI", ...}
  ],
  "total": 2
}
  ↓
// API Client (indicatorApi.list)
return response.indicators  // 배열 추출
  ↓
// 반환값
[
  {"indicator_id": 1, "name": "EMA", ...},
  {"indicator_id": 2, "name": "RSI", ...}
]  // ← Indicator[]
```

---

### Before (에러 발생)

```typescript
const data = await indicatorApi.list();
// data = [{"indicator_id": 1, ...}, ...]  (배열)

data.indicators  // ❌ undefined (배열에는 indicators 속성이 없음)
  ↓
data.indicators.length  // ❌ Cannot read properties of undefined
  ↓
💥 TypeError 발생
```

---

### After (정상 동작)

```typescript
const data = await indicatorApi.list();
// data = [{"indicator_id": 1, ...}, ...]  (배열)

data.length  // ✅ 5 (배열 길이)
  ↓
setAvailableIndicators(data)  // ✅ 정상
  ↓
console.log('[Builder] 지표 목록 로드 완료: 5 개')
console.log('[Builder] 커스텀 지표:', [
  {
    type: "custom_volume",
    output_fields: ["main", "vol_pos"]  // ✅ 2개!
  }
])
```

---

## 📊 다른 API와 비교

### 일관성 확인

#### Dataset API
```typescript
// api-client.ts
list: async () => {
  const response = await fetchApi<DatasetListResponse>('/api/datasets')
  return response.datasets  // ✅ 배열 반환
}

// 사용
const datasets = await datasetApi.list();
// datasets는 배열
```

#### Indicator API (수정 후)
```typescript
// api-client.ts
list: async () => {
  const response = await fetchApi<IndicatorListResponse>(endpoint)
  return response.indicators  // ✅ 배열 반환
}

// 사용
const indicators = await indicatorApi.list();
// indicators는 배열 (indicators.indicators 아님!)
```

---

## 🎯 영향 범위

### 수정된 파일
- `apps/web/app/strategies/builder/page.tsx` (1곳)

### 수정되지 않은 파일 (이미 올바름)
- ✅ `apps/web/app/strategies/builder/components/Step1_IndicatorSelector.tsx`
  ```typescript
  const data = await indicatorApi.list();
  setAvailableIndicators(data);  // ✅ 올바름
  ```

---

## ✅ 검증

### 수정 전 에러
```javascript
TypeError: Cannot read properties of undefined (reading 'length')
❌ availableIndicators = [] (업데이트 안 됨)
❌ ConditionRow에서 기본값 사용
❌ 1개만 표시
```

### 수정 후 정상
```javascript
✅ 에러 없음
✅ availableIndicators = [{...}, {...}, ...]
✅ ConditionRow에서 실제 output_fields 사용
✅ 2개 모두 표시
```

---

## 🧪 테스트 방법

### 1. 브라우저 새로고침
```
Ctrl + Shift + R
http://localhost:3000/strategies/builder
```

### 2. Console 확인

**기대되는 로그**:
```javascript
[Builder] 지표 목록 로드 완료: 5 개
[Builder] 커스텀 지표: [
  {
    type: "custom_volume",
    output_fields: ["main", "vol_pos"]  // ✅ 2개!
  }
]
```

### 3. 지표 추가 및 테스트

```
Step 1: custom_volume "+" 버튼
Step 2: "롱 조건 추가"
좌변 드롭다운 클릭
```

**Console 로그**:
```javascript
[ConditionRow-좌변] custom_volume_1 (custom_volume) → outputFields: (2) ["main", "vol_pos"]
  - 옵션: custom_volume_1.main (value: custom_volume_1)
  - 옵션: custom_volume_1.vol_pos (value: custom_volume_1_vol_pos)
```

**드롭다운 표시**:
```
━━━ 지표 ━━━
  custom_volume_1.main
  custom_volume_1.vol_pos
```

---

## 🎉 완료!

**핵심 수정**:
```typescript
// Before
const data = await indicatorApi.list();
setAvailableIndicators(data.indicators);  // ❌

// After
const data = await indicatorApi.list();
setAvailableIndicators(data);  // ✅
```

**이유**: `indicatorApi.list()`가 이미 배열을 반환하므로 직접 사용해야 함

---

**작성 일자**: 2025-12-13  
**수정 파일**: 1개  
**상태**: 완료 ✅

