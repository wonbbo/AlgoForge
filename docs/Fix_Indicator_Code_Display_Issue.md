# 지표 편집 페이지 코드 표시 문제 해결

## 📝 문제

지표 상세/편집 페이지(`/indicators/[type]`)에서 커스텀 지표의 코드가 표시되지 않는 문제가 있었습니다.

### 증상
- 수정 모드로 전환해도 코드 입력 창이 비어있음
- View 모드에서도 "코드를 보려면 수정 모드로 전환하세요" 메시지만 표시

### 원인
1. **백엔드 API**: `IndicatorResponse` 스키마에 `code` 필드가 없었음
2. **API 응답**: GET 엔드포인트에서 `code` 필드를 포함하지 않음
3. **프론트엔드 타입**: TypeScript `Indicator` 인터페이스에 `code` 필드 없음
4. **프론트엔드 로직**: `editData` 초기화 시 `code` 필드를 포함하지 않음

---

## ✅ 해결 방법

### 1. Backend: Pydantic 스키마 수정

**파일**: `apps/api/schemas/indicator.py`

```python
class IndicatorResponse(IndicatorBase):
    """지표 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    indicator_id: int = Field(..., description="지표 ID")
    implementation_type: str = Field(
        ..., 
        description="구현 타입: 'builtin' (내장) 또는 'custom' (커스텀)"
    )
    code: Optional[str] = Field(
        None,
        description="Python 함수 코드 (커스텀 지표인 경우만 포함)"  # ✅ 추가
    )
    params_schema: Optional[str] = Field(
        None, 
        description="파라미터 스키마 (JSON 문자열)"
    )
    # ... 나머지 필드
```

---

### 2. Backend: API 응답에 code 포함

**파일**: `apps/api/routers/indicators.py`

#### 2-1. 지표 목록 API 수정

```python
# 응답 생성
indicators = []
for row in rows:
    indicators.append(
        IndicatorResponse(
            indicator_id=row[0],
            name=row[1],
            type=row[2],
            description=row[3],
            category=row[4],
            implementation_type=row[5],
            code=row[6],  # ✅ 추가 (DB의 7번째 컬럼)
            params_schema=row[7],
            output_fields=json.loads(row[8]),
            created_at=row[9]
        )
    )
```

#### 2-2. 지표 상세 API 수정

```python
return IndicatorResponse(
    indicator_id=row[0],
    name=row[1],
    type=row[2],
    description=row[3],
    category=row[4],
    implementation_type=row[5],
    code=row[6],  # ✅ 추가
    params_schema=row[7],
    output_fields=json.loads(row[8]),
    created_at=row[9]
)
```

---

### 3. Frontend: TypeScript 타입 수정

**파일**: `apps/web/lib/types.ts`

```typescript
export interface Indicator {
  indicator_id: number
  name: string
  type: string
  description?: string
  category: 'trend' | 'momentum' | 'volatility' | 'volume'
  implementation_type: 'builtin' | 'custom'
  code?: string  // ✅ 추가: 커스텀 지표인 경우 Python 코드
  params_schema?: string
  output_fields: string[]
  created_at: number
}
```

---

### 4. Frontend: editData 초기화 수정

**파일**: `apps/web/app/indicators/[type]/page.tsx`

```typescript
// 수정 데이터 초기화
if (data.implementation_type === 'custom') {
  setEditData({
    name: data.name,
    description: data.description,
    code: data.code,              // ✅ 추가
    params_schema: data.params_schema,   // ✅ 추가
    output_fields: data.output_fields,   // ✅ 추가
  })
}
```

---

### 5. Frontend: View 모드에서 코드 표시

**파일**: `apps/web/app/indicators/[type]/page.tsx`

```typescript
// 이전 (문제)
<pre className="text-sm p-4 bg-muted rounded-md overflow-x-auto">
  <p className="text-muted-foreground">
    코드를 보려면 수정 모드로 전환하세요
  </p>
</pre>

// 이후 (해결)
<pre className="text-sm p-4 bg-muted rounded-md overflow-x-auto font-mono">
  {indicator.code || '// 코드 없음'}
</pre>
```

---

## 🔄 데이터 흐름

### Before (이전) ❌

```
DB (indicators 테이블)
  ├─ code: "def calculate_..."
  ↓
API Response
  ├─ ❌ code 필드 없음
  ↓
Frontend Indicator 타입
  ├─ ❌ code 필드 없음
  ↓
편집 페이지
  ├─ editData.code = undefined
  ├─ Textarea: 빈 화면
```

---

### After (이후) ✅

```
DB (indicators 테이블)
  ├─ code: "def calculate_..."
  ↓
API Response
  ├─ ✅ code: "def calculate_..."
  ↓
Frontend Indicator 타입
  ├─ ✅ code?: string
  ↓
편집 페이지
  ├─ editData.code = "def calculate_..."
  ├─ Textarea: 코드 표시됨
  ├─ View 모드: <pre>로 코드 표시
```

---

## 🧪 테스트 방법

### 1. 커스텀 지표 등록

```
http://localhost:5001/indicators/new
```

1. 지표 정보 입력
2. 코드 입력:
   ```python
   def calculate_my_indicator(df, params):
       period = params.get('period', 20)
       return df['close'].rolling(window=period).mean().fillna(0)
   ```
3. "등록" 버튼 클릭

---

### 2. 지표 상세 페이지 확인

```
http://localhost:5001/indicators/[등록한_지표_type]
```

**확인 사항**:
- ✅ Python 코드 섹션에 코드가 표시됨
- ✅ 코드가 `<pre>` 태그로 포맷되어 표시됨

---

### 3. 편집 모드 확인

1. "수정" 버튼 클릭
2. **확인 사항**:
   - ✅ 이름 필드에 기존 값 표시
   - ✅ 설명 필드에 기존 값 표시
   - ✅ **코드 입력창에 기존 코드 표시** (가장 중요!)
   - ✅ 코드를 수정할 수 있음
3. 코드 수정 후 "코드 검증" 버튼 클릭
4. "저장" 버튼 클릭

---

### 4. API 직접 테스트

```bash
# 지표 조회
curl http://localhost:6000/api/indicators/custom_volume

# 응답 확인
{
  "indicator_id": 26,
  "name": "CustomVolume",
  "type": "custom_volume",
  "description": "...",
  "category": "volume",
  "implementation_type": "custom",
  "code": "def calculate_custom_volume(df, params): ...",  # ✅ 코드 포함
  "params_schema": "{\"ema_period\": 20}",
  "output_fields": ["main", "vol_pos"],
  "created_at": 1765611191
}
```

---

## 📊 수정된 파일

### Backend (2개)
1. `apps/api/schemas/indicator.py`
   - `IndicatorResponse`에 `code` 필드 추가

2. `apps/api/routers/indicators.py`
   - `list_indicators`: row[6] (code) 포함
   - `get_indicator`: row[6] (code) 포함

### Frontend (2개)
1. `apps/web/lib/types.ts`
   - `Indicator` 인터페이스에 `code?: string` 추가

2. `apps/web/app/indicators/[type]/page.tsx`
   - `editData` 초기화 시 code 포함
   - View 모드에서 코드 표시

---

## 🎯 결과

### Before (이전)
```
편집 모드 진입
  ↓
코드 입력창: [ 빈 화면 ]
  ↓
사용자: ❌ 기존 코드를 볼 수 없음
```

### After (이후)
```
편집 모드 진입
  ↓
코드 입력창: [ def calculate_...(기존 코드) ]
  ↓
사용자: ✅ 기존 코드를 보고 수정 가능
```

---

## 🔒 보안 고려사항

### 현재 구현 (MVP)
- ✅ 코드를 API 응답에 포함 (개인 사용이므로 OK)
- ✅ 코드 검증기로 위험한 코드 차단
- ✅ 허용된 라이브러리만 import 가능

### 프로덕션 환경 권장사항
- 🔐 별도의 코드 조회 엔드포인트 분리
- 🔐 인증/권한 확인
- 🔐 코드 암호화 저장
- 🔐 샌드박스 환경에서 실행

---

## ✅ 체크리스트

- [x] Backend: `IndicatorResponse` 스키마에 code 추가
- [x] Backend: API 응답에 code 포함 (2곳)
- [x] Frontend: TypeScript 타입에 code 추가
- [x] Frontend: editData 초기화 시 code 포함
- [x] Frontend: View 모드에서 코드 표시
- [x] Lint 검사 통과
- [x] 문서 작성

---

## 🎉 완료!

이제 지표 편집 페이지에서 등록된 코드를 정상적으로 확인하고 수정할 수 있습니다!

**테스트**:
1. 기존 커스텀 지표 상세 페이지 접속
2. 코드가 표시되는지 확인 ✅
3. "수정" 버튼 클릭
4. 코드 입력창에 기존 코드가 표시되는지 확인 ✅

---

**수정 일자**: 2025-12-13  
**수정 파일**: 4개  
**영향 범위**: 지표 상세/편집 페이지  
**상태**: 완료 ✅

