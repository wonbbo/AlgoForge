# 지표 편집 시 파라미터 수정 기능 추가

## 📝 개요

지표 상세/편집 페이지에서 커스텀 지표의 **모든 설정**을 수정할 수 있도록 기능을 확장했습니다.

### 추가된 편집 기능
- ✅ 카테고리 (trend/momentum/volatility/volume)
- ✅ 파라미터 스키마 (JSON)
- ✅ 출력 필드 (main, signal, histogram 등)

### 기존 편집 기능
- 지표 이름
- 설명
- Python 코드

---

## 🎯 변경 사항

### Before (이전) ❌

**편집 가능**:
- 이름
- 설명
- 코드

**읽기 전용**:
- 카테고리 (수정 불가)
- 파라미터 스키마 (수정 불가)
- 출력 필드 (수정 불가)

**문제점**: 지표 등록 시 파라미터나 출력 필드를 잘못 입력하면 삭제 후 재등록해야 함

---

### After (현재) ✅

**모두 편집 가능**:
- 이름 (Input)
- 설명 (Textarea)
- 카테고리 (Select dropdown)
- 파라미터 스키마 (Textarea, JSON 형식)
- 출력 필드 (Input, 쉼표로 구분)
- Python 코드 (Textarea)

**장점**: 지표 등록 후에도 모든 설정을 자유롭게 수정 가능

---

## 🔧 구현 상세

### 1. Backend: Pydantic 스키마 수정

**파일**: `apps/api/schemas/indicator.py`

```python
class CustomIndicatorUpdate(BaseModel):
    """커스텀 지표 수정 요청 스키마"""
    name: Optional[str] = Field(None, description="지표 이름")
    description: Optional[str] = Field(None, description="지표 설명")
    category: Optional[str] = Field(
        None, 
        description="카테고리: trend/momentum/volatility/volume"
    )  # ✅ 추가
    code: Optional[str] = Field(None, description="Python 함수 코드")
    params_schema: Optional[str] = Field(None, description="파라미터 스키마")
    output_fields: Optional[List[str]] = Field(None, description="출력 필드명 목록")
```

---

### 2. Backend: Update 엔드포인트 수정

**파일**: `apps/api/routers/indicators.py`

#### 카테고리 유효성 검증 추가

```python
if update_data.category is not None:
    # 카테고리 유효성 검증
    valid_categories = ['trend', 'momentum', 'volatility', 'volume']
    if update_data.category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 카테고리입니다. 허용된 값: {', '.join(valid_categories)}"
        )
    update_fields.append("category = ?")
    update_values.append(update_data.category)
```

**검증 내용**:
- ✅ params_schema: JSON 파싱 검증 (기존)
- ✅ category: 허용된 값 검증 (추가)
- ✅ code: 코드 검증기로 보안 검증 (기존)

---

### 3. Frontend: TypeScript 타입 수정

**파일**: `apps/web/lib/types.ts`

```typescript
export interface IndicatorUpdate {
  name?: string
  description?: string
  category?: string  // ✅ 추가
  code?: string
  params_schema?: string
  output_fields?: string[]
}
```

---

### 4. Frontend: UI 구현

**파일**: `apps/web/app/indicators/[type]/page.tsx`

#### 4-1. editData 초기화 수정

```typescript
// 수정 데이터 초기화
if (data.implementation_type === 'custom') {
  setEditData({
    name: data.name,
    description: data.description,
    category: data.category,           // ✅ 추가
    code: data.code,
    params_schema: data.params_schema,  // ✅ 추가
    output_fields: data.output_fields,  // ✅ 추가
  })
}
```

---

#### 4-2. 카테고리 선택 UI

```typescript
<div className="flex-1">
  <Label>카테고리</Label>
  {isEditing ? (
    <select
      value={editData.category || indicator.category}
      onChange={e => setEditData({...editData, category: e.target.value as any})}
      className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm mt-1"
    >
      <option value="trend">Trend (추세)</option>
      <option value="momentum">Momentum (모멘텀)</option>
      <option value="volatility">Volatility (변동성)</option>
      <option value="volume">Volume (거래량)</option>
    </select>
  ) : (
    <p className="text-sm mt-1">
      <Badge variant="outline">{indicator.category}</Badge>
    </p>
  )}
</div>
```

---

#### 4-3. 출력 필드 입력 UI

```typescript
<div>
  <Label>출력 필드</Label>
  <Input
    value={editData.output_fields?.join(', ') || ''}
    onChange={e => {
      const fields = e.target.value.split(',').map(f => f.trim()).filter(f => f)
      setEditData({...editData, output_fields: fields})
    }}
    placeholder="main, signal, histogram (쉼표로 구분)"
  />
  <p className="text-xs text-muted-foreground mt-1">
    쉼표(,)로 구분하여 입력하세요. 예: main, signal, histogram
  </p>
</div>
```

**처리 로직**:
- 입력값을 쉼표로 분리
- 각 필드명을 trim하여 공백 제거
- 빈 문자열 필터링

---

#### 4-4. 파라미터 스키마 입력 UI

```typescript
<div>
  <Label>파라미터 스키마</Label>
  <Textarea
    value={editData.params_schema || ''}
    onChange={e => setEditData({...editData, params_schema: e.target.value})}
    rows={4}
    className="font-mono text-sm"
    placeholder='{"period": 20, "source": "close"}'
  />
  <p className="text-xs text-muted-foreground mt-1">
    JSON 형식으로 입력하세요. 기본 파라미터 값을 포함해야 합니다.
  </p>
</div>
```

---

#### 4-5. 저장 시 검증 로직

```typescript
const handleSave = async () => {
  // 1. 코드 검증 (기존)
  if (editData.code && !validationResult?.is_valid) {
    alert('코드 수정 시 검증을 통과해야 합니다')
    return
  }
  
  // 2. params_schema JSON 검증 (추가)
  if (editData.params_schema) {
    try {
      JSON.parse(editData.params_schema)
    } catch (err) {
      alert('파라미터 스키마가 올바른 JSON 형식이 아닙니다')
      return
    }
  }
  
  // 3. output_fields 검증 (추가)
  if (editData.output_fields && editData.output_fields.length === 0) {
    alert('최소 하나의 출력 필드가 필요합니다')
    return
  }
  
  // ... API 호출
}
```

---

## 📊 사용 예시

### 예시 1: 파라미터 스키마 수정

**기존 지표**:
```json
{
  "name": "Custom EMA",
  "params_schema": "{\"period\": 20}"
}
```

**수정 필요**: source 파라미터 추가

**편집 화면**:
```
파라미터 스키마:
┌──────────────────────────────────────┐
│ {"period": 20, "source": "close"}    │
└──────────────────────────────────────┘
```

**저장 후**:
```json
{
  "params_schema": "{\"period\": 20, \"source\": \"close\"}"
}
```

---

### 예시 2: 출력 필드 변경

**기존 지표**:
```json
{
  "name": "Simple Indicator",
  "output_fields": ["main"]
}
```

**수정 필요**: signal 필드 추가하여 2개 출력으로 변경

**편집 화면**:
```
출력 필드:
┌──────────────────────────────────────┐
│ main, signal                         │
└──────────────────────────────────────┘
쉼표(,)로 구분하여 입력하세요
```

**저장 후**:
```json
{
  "output_fields": ["main", "signal"]
}
```

**주의**: 코드도 함께 수정해야 함!
```python
# 수정된 코드
def calculate_simple_indicator(df, params):
    # ... 계산 로직
    return {
        'main': main_series,
        'signal': signal_series  # 추가
    }
```

---

### 예시 3: 카테고리 변경

**상황**: 지표를 잘못된 카테고리로 등록

**편집 화면**:
```
카테고리:
┌──────────────────────────────────────┐
│ [v] Trend (추세)         ▼           │
│     Momentum (모멘텀)                │
│     Volatility (변동성)              │
│     Volume (거래량)                  │
└──────────────────────────────────────┘
```

**드롭다운에서 선택** → "저장" → 즉시 반영

---

## 🔄 데이터 흐름

### 1. 초기 로딩

```
API: GET /api/indicators/custom_volume
  ↓
Response:
{
  "name": "CustomVolume",
  "category": "volume",
  "params_schema": "{\"ema_period\": 20}",
  "output_fields": ["main", "vol_pos"],
  "code": "def calculate_..."
}
  ↓
editData 초기화:
{
  name: "CustomVolume",
  category: "volume",
  params_schema: "{\"ema_period\": 20}",
  output_fields: ["main", "vol_pos"],
  code: "def calculate_..."
}
  ↓
UI 렌더링 (편집 모드 시 모든 필드 입력 가능)
```

---

### 2. 수정 및 저장

```
사용자 편집:
- 카테고리: volume → momentum
- 파라미터: {"ema_period": 20} → {"ema_period": 20, "threshold": 0.5}
- 출력 필드: main, vol_pos → main, vol_pos, strength
  ↓
프론트엔드 검증:
- params_schema JSON 파싱 ✅
- output_fields 개수 확인 ✅
  ↓
API: PATCH /api/indicators/custom_volume
Body: {
  "category": "momentum",
  "params_schema": "{\"ema_period\": 20, \"threshold\": 0.5}",
  "output_fields": ["main", "vol_pos", "strength"]
}
  ↓
백엔드 검증:
- category 허용값 확인 ✅
- params_schema JSON 파싱 ✅
  ↓
DB 업데이트:
UPDATE indicators SET
  category = ?,
  params_schema = ?,
  output_fields = ?,
  updated_at = ?
WHERE type = ?
  ↓
성공 응답 → UI 업데이트
```

---

## ⚠️ 주의사항

### 1. 출력 필드 변경 시

**문제**: 출력 필드를 변경하면 기존 전략이 깨질 수 있음

**예시**:
```
기존: output_fields = ["main"]
전략에서 사용: "custom_indicator_1"

수정 후: output_fields = ["main", "signal"]
전략에서 사용: "custom_indicator_1" → 여전히 main 참조 (OK)
             "custom_indicator_1_signal" → 새로운 필드 (추가 가능)
```

**권장**:
- 출력 필드 추가는 안전 (기존 필드는 유지)
- 출력 필드 삭제/이름 변경은 주의 필요

---

### 2. 파라미터 스키마 변경 시

**문제**: 파라미터를 제거하면 기존 전략이 에러 발생 가능

**예시**:
```
기존: {"period": 20, "source": "close"}
전략에서 사용: custom_indicator_1 (params에 period, source 기대)

수정 후: {"threshold": 0.5}
전략 실행 시: period, source가 없어서 에러!
```

**권장**:
- 파라미터 추가는 안전 (기본값 설정)
- 파라미터 제거는 코드도 함께 수정
- 파라미터 이름 변경 시 코드 수정 필수

---

### 3. 코드와 설정 일치 필수

**중요**: 코드와 params_schema, output_fields는 항상 일치해야 함

**잘못된 예**:
```python
# 코드
def calculate(df, params):
    period = params.get('period', 20)  # period 사용
    return df['close'].rolling(period).mean()

# params_schema (잘못됨!)
{"threshold": 0.5}  # period가 없음!
```

**올바른 예**:
```python
# 코드
def calculate(df, params):
    period = params.get('period', 20)
    return df['close'].rolling(period).mean()

# params_schema (올바름!)
{"period": 20}  # 코드와 일치
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 단일 출력 → 다중 출력 변경

1. **기존 지표 확인**
   - `http://localhost:3000/indicators/my_simple_ema`
   - output_fields: `["main"]`

2. **편집 모드 진입**
   - "수정" 버튼 클릭

3. **출력 필드 수정**
   - 입력: `main, upper, lower`
   - 실시간 파싱: `["main", "upper", "lower"]`

4. **코드 수정**
```python
def calculate_my_simple_ema(df, params):
    period = params.get('period', 20)
    ema = df['close'].ewm(span=period).mean()
    std = df['close'].rolling(period).std()
    
    return {
        'main': ema.fillna(0),
        'upper': (ema + std).fillna(0),
        'lower': (ema - std).fillna(0)
    }
```

5. **코드 검증 → 저장**

6. **확인**
   - 전략 빌더에서 `my_simple_ema_1.my_simple_ema`, `my_simple_ema_1.upper`, `my_simple_ema_1.lower` 선택 가능

---

### 시나리오 2: 카테고리 변경

1. **지표 확인**
   - `http://localhost:3000/indicators/momentum_indicator`
   - category: `volume` (잘못 등록됨)

2. **편집 모드**
   - 카테고리 드롭다운: `Momentum (모멘텀)` 선택

3. **저장**
   - ✅ 즉시 반영

4. **확인**
   - 지표 목록 페이지에서 "Momentum" 필터링 시 표시됨

---

### 시나리오 3: 파라미터 추가

1. **기존 파라미터**
```json
{"period": 20}
```

2. **편집**
```json
{"period": 20, "multiplier": 2.0, "source": "close"}
```

3. **코드 수정**
```python
def calculate(df, params):
    period = params.get('period', 20)
    multiplier = params.get('multiplier', 2.0)  # 추가
    source = params.get('source', 'close')      # 추가
    
    # ... 계산 로직
```

4. **검증 → 저장**

---

## ✅ 체크리스트

### Backend
- [x] `CustomIndicatorUpdate`에 category 추가
- [x] Update 엔드포인트에 category 검증 추가
- [x] Category 허용값 검증 로직 구현

### Frontend
- [x] `IndicatorUpdate` 타입에 category 추가
- [x] editData 초기화 시 모든 필드 포함
- [x] 카테고리 선택 UI (select dropdown)
- [x] 출력 필드 입력 UI (comma-separated)
- [x] 파라미터 스키마 입력 UI (JSON textarea)
- [x] 저장 시 JSON 검증 로직
- [x] 저장 시 출력 필드 검증 로직

### 검증
- [x] Lint 에러 0개
- [x] TypeScript 컴파일 성공
- [x] 모든 필드 편집 가능 확인

---

## 📚 관련 문서

- [Indicator Management System Implementation](./Indicator_Management_System_Implementation_Summary.md)
- [Fix Indicator Code Display Issue](./Fix_Indicator_Code_Display_Issue.md)
- [Custom Indicators Complete Guide](./Custom_Indicators_Complete_Guide.md)

---

## 🎉 완료!

이제 지표 편집 페이지에서 **모든 설정**을 자유롭게 수정할 수 있습니다:

- ✅ 이름
- ✅ 설명
- ✅ 카테고리 (드롭다운)
- ✅ 파라미터 스키마 (JSON)
- ✅ 출력 필드 (쉼표 구분)
- ✅ Python 코드

**테스트**: 커스텀 지표를 수정하고 전략에서 정상 작동하는지 확인하세요!

---

**작성 일자**: 2025-12-13  
**수정 파일**: 4개  
**상태**: 완료 ✅

