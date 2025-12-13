# 지표 라이브러리 출력 필드 표시 수정

## 📝 문제

지표 라이브러리 페이지(`/indicators`)에서 커스텀 지표의 출력 필드가 제대로 표시되지 않고 지표 타입명이 표시되고 있었습니다.

### 증상

**Before (이전)** ❌
```
지표 카드:
┌──────────────────────────────┐
│ CustomVolume         [커스텀] │
│                               │
│ 볼륨과 볼륨 EMA 비교...       │
│                               │
│ [volume] [custom_volume]      │ ← 지표 타입명 표시
│                               │
└──────────────────────────────┘
```

**문제점**:
- 출력 필드(main, vol_pos)가 표시되지 않음
- 대신 지표 타입명(custom_volume)이 표시됨
- 다중 출력인지 알 수 없음 (출력 개수 배지만 표시)

---

## ✅ 해결 방법

### 수정된 코드

**파일**: `apps/web/app/indicators/page.tsx`

#### Before (문제)
```typescript
<div className="flex flex-wrap gap-2">
  <Badge variant="outline" className="text-xs">
    {indicator.category}
  </Badge>
  <Badge variant="outline" className="text-xs">
    {indicator.type}  {/* ❌ 지표 타입명 */}
  </Badge>
  {indicator.output_fields.length > 1 && (
    <Badge variant="outline" className="text-xs">
      {indicator.output_fields.length} 출력  {/* 개수만 표시 */}
    </Badge>
  )}
</div>
```

#### After (해결)
```typescript
<div className="flex flex-wrap gap-2">
  <Badge variant="outline" className="text-xs">
    {indicator.category}
  </Badge>
  {indicator.output_fields.map(field => (
    <Badge key={field} variant="outline" className="text-xs">
      출력: {field}  {/* ✅ 각 출력 필드 표시 */}
    </Badge>
  ))}
  {indicator.output_fields.length > 1 && (
    <Badge variant="outline" className="text-xs font-semibold">
      {indicator.output_fields.length}개 출력  {/* 요약 정보 */}
    </Badge>
  )}
</div>
```

---

## 📊 비교

### Before (이전) ❌

#### 내장 지표 (EMA)
```
┌──────────────────────────────┐
│ EMA                   [내장]  │
│ Exponential Moving Average   │
│ [trend] [ema]                │ ← 지표 타입명
└──────────────────────────────┘
```

#### 커스텀 지표 (단일 출력)
```
┌──────────────────────────────┐
│ My Indicator         [커스텀] │
│ 내 커스텀 지표               │
│ [momentum] [my_indicator]    │ ← 지표 타입명
└──────────────────────────────┘
```

#### 커스텀 지표 (다중 출력)
```
┌──────────────────────────────┐
│ CustomVolume         [커스텀] │
│ 볼륨 분석 지표               │
│ [volume] [custom_volume]     │ ← 지표 타입명
│ [2 출력]                     │ ← 개수만 표시
└──────────────────────────────┘
```

**문제**: 어떤 필드들이 출력되는지 알 수 없음!

---

### After (현재) ✅

#### 내장 지표 (EMA)
```
┌──────────────────────────────┐
│ EMA                   [내장]  │
│ Exponential Moving Average   │
│ [trend] [출력: main]         │ ← 출력 필드명
└──────────────────────────────┘
```

#### 커스텀 지표 (단일 출력)
```
┌──────────────────────────────┐
│ My Indicator         [커스텀] │
│ 내 커스텀 지표               │
│ [momentum] [출력: main]      │ ← 출력 필드명
└──────────────────────────────┘
```

#### 커스텀 지표 (다중 출력)
```
┌──────────────────────────────────────┐
│ CustomVolume               [커스텀]   │
│ 볼륨 분석 지표                       │
│ [volume] [출력: main]                │ ← 명확!
│ [출력: vol_pos] [2개 출력]           │
└──────────────────────────────────────┘
```

**개선**: 모든 출력 필드가 명확하게 표시됨!

---

## 🎨 UI 개선 효과

### 단일 출력 지표

**Before**:
- 카테고리 배지
- 지표 타입 배지 (불필요)

**After**:
- 카테고리 배지
- 출력 필드 배지 (유용)

---

### 다중 출력 지표 (MACD)

**Before**:
```
[momentum] [custom_macd] [3 출력]
```
- "3개가 뭐지?"
- "어떤 필드들이지?"

**After**:
```
[momentum] [출력: main] [출력: signal] [출력: histogram] [3개 출력]
```
- "main, signal, histogram 3개구나!"
- "전략에서 이걸 사용할 수 있겠네!"

---

## 📋 예시

### 예시 1: EMA (내장 지표)

**지표 정보**:
```json
{
  "name": "EMA",
  "type": "ema",
  "category": "trend",
  "output_fields": ["main"]
}
```

**지표 카드 표시**:
```
┌──────────────────────────────┐
│ EMA                   [내장]  │
│ Exponential Moving Average   │
│                               │
│ [trend] [출력: main]          │
│                               │
└──────────────────────────────┘
```

---

### 예시 2: CustomVolume (다중 출력)

**지표 정보**:
```json
{
  "name": "CustomVolume",
  "type": "custom_volume",
  "category": "volume",
  "output_fields": ["main", "vol_pos"]
}
```

**지표 카드 표시**:
```
┌──────────────────────────────────────┐
│ CustomVolume               [커스텀]   │
│ 볼륨과 볼륨 EMA 비교                 │
│                                       │
│ [volume] [출력: main]                 │
│ [출력: vol_pos] [2개 출력]            │
│                                       │
└──────────────────────────────────────┘
```

---

### 예시 3: Custom MACD (3개 출력)

**지표 정보**:
```json
{
  "name": "Custom MACD",
  "type": "custom_macd",
  "category": "momentum",
  "output_fields": ["main", "signal", "histogram"]
}
```

**지표 카드 표시**:
```
┌────────────────────────────────────────────┐
│ Custom MACD                     [커스텀]    │
│ MACD 지표                                  │
│                                             │
│ [momentum] [출력: main]                     │
│ [출력: signal] [출력: histogram]            │
│ [3개 출력]                                  │
│                                             │
└────────────────────────────────────────────┘
```

---

## 🎯 사용자 경험 개선

### Before (혼란스러움)

**사용자 생각**:
- "custom_volume은 지표 이름 아닌가?"
- "2 출력이라는데 뭐가 2개지?"
- "어떤 필드를 사용할 수 있는지 모르겠네"
- "상세 페이지를 클릭해야 알 수 있구나..."

---

### After (명확함)

**사용자 생각**:
- "main과 vol_pos 필드가 있구나!"
- "전략에서 custom_volume_1.main이랑 custom_volume_1.vol_pos를 쓸 수 있겠네"
- "클릭하지 않아도 한눈에 알 수 있어서 좋다"
- "지표를 비교하기 쉽네"

---

## 🔄 데이터 흐름

### 렌더링 로직

```typescript
// 1. 카테고리 배지
<Badge variant="outline" className="text-xs">
  {indicator.category}
</Badge>

// 2. 각 출력 필드 배지
{indicator.output_fields.map(field => (
  <Badge key={field} variant="outline" className="text-xs">
    출력: {field}
  </Badge>
))}

// 3. 다중 출력 요약 배지 (2개 이상일 때만)
{indicator.output_fields.length > 1 && (
  <Badge variant="outline" className="text-xs font-semibold">
    {indicator.output_fields.length}개 출력
  </Badge>
)}
```

---

### 예시 렌더링

#### 단일 출력
```
input: ["main"]
  ↓
output:
  - <Badge>출력: main</Badge>
  - (개수 배지 없음)
```

#### 다중 출력
```
input: ["main", "vol_pos"]
  ↓
output:
  - <Badge>출력: main</Badge>
  - <Badge>출력: vol_pos</Badge>
  - <Badge font-semibold>2개 출력</Badge>  (요약)
```

---

## ✅ 검증

### 테스트 시나리오 1: 내장 지표 확인

```
1. http://localhost:3000/indicators 접속
2. "내장" 필터 선택
3. EMA 카드 확인

✅ 배지: [trend] [출력: main]
✅ "출력: main" 명확히 표시
```

---

### 테스트 시나리오 2: 단일 출력 커스텀 지표

```
1. http://localhost:3000/indicators 접속
2. "커스텀" 필터 선택
3. 단일 출력 지표 카드 확인

✅ 배지: [category] [출력: main]
✅ 개수 배지 없음 (단일 출력)
```

---

### 테스트 시나리오 3: 다중 출력 커스텀 지표

```
1. http://localhost:3000/indicators 접속
2. "커스텀" 필터 선택
3. CustomVolume 카드 확인

✅ 배지: [volume] [출력: main] [출력: vol_pos] [2개 출력]
✅ 모든 출력 필드 명확히 표시
✅ "2개 출력" 요약 배지로 강조
```

---

## 🎨 디자인 고려사항

### 배지 스타일

```typescript
// 일반 출력 필드
<Badge variant="outline" className="text-xs">
  출력: {field}
</Badge>

// 개수 요약 (강조)
<Badge variant="outline" className="text-xs font-semibold">
  {indicator.output_fields.length}개 출력
</Badge>
```

**차이점**:
- 개수 배지는 `font-semibold`로 강조
- 시각적으로 구분하여 요약 정보임을 표시

---

### 레이아웃

```
flex flex-wrap gap-2
```

**효과**:
- 배지가 많아도 자동으로 줄바꿈
- 2px 간격으로 깔끔하게 배치
- 반응형 디자인 지원

---

## 📚 관련 개선사항

### 일관성 확보

#### 지표 라이브러리 페이지 (수정됨)
```
✅ [카테고리] [출력: field1] [출력: field2] [N개 출력]
```

#### 지표 상세 페이지 (기존 유지)
```
출력 필드:
  [main] [signal] [histogram]
```

#### 전략 빌더 (기존 유지)
```
지표 선택:
  - indicator_1.main
  - indicator_1.signal
  - indicator_1.histogram
```

**일관성**: 모든 페이지에서 출력 필드를 명확하게 표시

---

## 📝 수정 파일

**파일**: `apps/web/app/indicators/page.tsx`

**수정 위치**: 162-174번 줄 (배지 렌더링 부분)

**변경 내용**:
- 지표 타입 배지 제거
- 출력 필드 배지 추가 (map으로 모든 필드 표시)
- 개수 배지 텍스트 수정 ("2 출력" → "2개 출력")
- 개수 배지에 font-semibold 추가

---

## 🎯 요약

### 문제
- 지표 라이브러리에서 출력 필드 대신 지표 타입명이 표시됨
- 다중 출력 지표의 필드를 확인하려면 상세 페이지로 이동해야 함

### 해결
- 모든 출력 필드를 배지로 표시
- "출력: field" 형식으로 명확하게 표시
- 다중 출력 시 "N개 출력" 요약 배지 추가

### 결과
- ✅ 한눈에 출력 필드 확인 가능
- ✅ 지표 비교 용이
- ✅ 전략 빌더에서 사용할 필드 미리 파악
- ✅ 사용자 경험 향상

---

## 🎉 완료!

이제 지표 라이브러리에서 각 지표의 출력 필드를 명확하게 확인할 수 있습니다!

**테스트**: `/indicators` 페이지에서 커스텀 지표 카드를 확인하세요!

---

**작성 일자**: 2025-12-13  
**수정 파일**: 1개  
**수정 줄 수**: 12줄  
**상태**: 완료 ✅

