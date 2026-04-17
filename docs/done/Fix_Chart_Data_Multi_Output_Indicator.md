# 차트 데이터 API 다중 출력 지표 지원

## 📝 문제

차트 데이터 API에서 다중 출력 커스텀 지표의 데이터를 추출하지 못하는 문제:

```
WARNING: 지표 c_vol 값 추출 실패: 지표 'c_vol'가 계산되지 않았습니다
```

---

## 🔍 원인 분석

### 문제 코드 (Before)

**위치**: `apps/api/routers/runs.py` - `get_chart_data` 엔드포인트

```python
# 지표 데이터 추출
for indicator in strategy_indicators:
    indicator_id = indicator.get("id")  # "c_vol"
    
    # 문제: indicator_id를 직접 컬럼명으로 사용
    for i in range(start_idx, end_idx + 1):
        value = strategy_parser.indicator_calc.get_value(indicator_id, i)
        # ❌ DataFrame에 "c_vol" 컬럼이 없음!
        # ✅ 실제 컬럼: "c_vol_vma", "c_vol_vmf"
```

### 문제 상황

```
지표 정의:
- ID: c_vol
- Type: cvol
- Output Fields: ["vma", "vmf"]

DataFrame 컬럼:
- c_vol_vma ✅ (존재)
- c_vol_vmf ✅ (존재)
- c_vol ❌ (존재하지 않음!)

API 호출:
get_value("c_vol", i) → ValueError: 지표 'c_vol'가 계산되지 않았습니다
```

---

## ✅ 해결 방법

### 1️⃣ 지표 메타 정보 로드

지표 타입별로 `output_fields`를 DB에서 조회:

```python
# 지표 메타 정보 로드 (output_fields 확인용)
indicators_metadata = {}
try:
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT type, output_fields FROM indicators")
        for row in cursor.fetchall():
            indicators_metadata[row[0]] = json.loads(row[1])
except Exception as e:
    logger.warning(f"지표 메타 정보 로드 실패: {e}")
```

**결과**:
```python
indicators_metadata = {
    "ema": ["main"],
    "cvol": ["vma", "vmf"],
    ...
}
```

---

### 2️⃣ 각 출력 필드별 데이터 추출

```python
for indicator in strategy_indicators:
    indicator_id = indicator.get("id")      # "c_vol"
    indicator_type = indicator.get("type")  # "cvol"
    
    # 지표의 output_fields 확인
    output_fields = indicators_metadata.get(indicator_type, ["main"])
    # output_fields = ["vma", "vmf"]
    
    # 각 output_field별로 데이터 추출
    for field in output_fields:
        # 컬럼명 생성
        if len(output_fields) == 1 and field == "main":
            column_name = indicator_id         # "ema_1"
            display_key = indicator_id         # "ema_1"
        else:
            column_name = f"{indicator_id}_{field}"  # "c_vol_vma", "c_vol_vmf"
            display_key = f"{indicator_id}.{field}"  # "c_vol.vma", "c_vol.vmf"
        
        # 지표 값 추출
        try:
            indicator_values = []
            for i in range(start_idx, end_idx + 1):
                value = strategy_parser.indicator_calc.get_value(column_name, i)
                indicator_values.append(value)
            
            indicators_data[display_key] = indicator_values
            indicator_types[display_key] = classify_indicator_display_type(indicator_type)
        except Exception as e:
            logger.warning(f"지표 {display_key} (컬럼: {column_name}) 값 추출 실패: {e}")
```

---

## 📊 데이터 흐름

### Before (에러)

```python
Strategy:
├─ indicators: [{"id": "c_vol", "type": "cvol"}]

DataFrame:
├─ c_vol_vma: [100, 102, ...]  ✅
├─ c_vol_vmf: [1, 1, -1, ...]  ✅

API 추출:
├─ get_value("c_vol", i) → ❌ ValueError!

Response:
├─ indicators_data: {} (빈 객체)
```

---

### After (정상)

```python
Strategy:
├─ indicators: [{"id": "c_vol", "type": "cvol"}]

Metadata:
├─ cvol: ["vma", "vmf"]

DataFrame:
├─ c_vol_vma: [100, 102, ...]  ✅
├─ c_vol_vmf: [1, 1, -1, ...]  ✅

API 추출:
├─ for field in ["vma", "vmf"]:
│   ├─ column_name = "c_vol_vma" → get_value("c_vol_vma", i) ✅
│   ├─ column_name = "c_vol_vmf" → get_value("c_vol_vmf", i) ✅

Response:
├─ indicators_data: {
│   ├─ "c_vol.vma": [100, 102, 104, ...],
│   └─ "c_vol.vmf": [1, 1, -1, 1, ...]
│   }
├─ indicator_types: {
│   ├─ "c_vol.vma": "overlay",
│   └─ "c_vol.vmf": "oscillator"
│   }
```

---

## 🎯 주요 변경 사항

### 1. Import 추가

```python
# apps/api/routers/runs.py
import json  # JSON 파싱용
```

---

### 2. 지표 메타 정보 로드

```python
# 지표 메타 정보 로드 (output_fields 확인용)
indicators_metadata = {}
try:
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT type, output_fields FROM indicators")
        for row in cursor.fetchall():
            indicators_metadata[row[0]] = json.loads(row[1])
except Exception as e:
    logger.warning(f"지표 메타 정보 로드 실패: {e}")
```

---

### 3. 출력 필드별 데이터 추출

```python
# 지표의 output_fields 확인
output_fields = indicators_metadata.get(indicator_type, ["main"])

# 각 output_field별로 데이터 추출
for field in output_fields:
    # 컬럼명 생성
    if len(output_fields) == 1 and field == "main":
        column_name = indicator_id
        display_key = indicator_id
    else:
        column_name = f"{indicator_id}_{field}"
        display_key = f"{indicator_id}.{field}"
```

---

### 4. Display Key 형식

프론트엔드에서 사용할 키 형식을 **점(.) 구분자**로 통일:

```python
# 단일 출력
display_key = "ema_1"  # 그대로

# 다중 출력
display_key = "c_vol.vma"   # indicator_id.field
display_key = "c_vol.vmf"   # indicator_id.field
```

**장점**:
- 프론트엔드 조건 입력과 동일한 형식
- 명확한 필드 구분
- 일관된 API 응답 형식

---

## 🧪 테스트

### 1️⃣ API 서버 재시작

```bash
stop_server.bat
start_server.bat
```

---

### 2️⃣ 차트 데이터 API 호출

```http
GET /api/runs/{run_id}/charts/{trade_index}
```

**기대 응답**:

```json
{
  "ohlcv": [...],
  "indicators_data": {
    "c_vol.vma": [100.5, 102.3, ...],
    "c_vol.vmf": [1, 1, -1, 1, ...]
  },
  "indicator_types": {
    "c_vol.vma": "overlay",
    "c_vol.vmf": "oscillator"
  },
  "trade_info": {...}
}
```

---

### 3️⃣ 프론트엔드 차트 렌더링

```typescript
// 차트 데이터 처리
Object.entries(chartData.indicators_data).forEach(([key, values]) => {
  // key = "c_vol.vma" 또는 "c_vol.vmf"
  // values = [100.5, 102.3, ...]
  
  const type = chartData.indicator_types[key];  // "overlay" 또는 "oscillator"
  
  if (type === "overlay") {
    // 가격 차트에 오버레이
  } else {
    // 별도 오실레이터 차트
  }
});
```

---

## 📝 추가 고려사항

### 1. 성능 최적화

현재는 각 차트 요청마다 지표 메타 정보를 로드합니다.

**개선 방안** (향후):
- 서버 시작 시 메모리에 캐시
- 지표 변경 시 캐시 무효화

```python
# 글로벌 캐시 (서버 시작 시 로드)
INDICATORS_METADATA_CACHE = {}

def load_indicators_metadata():
    """서버 시작 시 호출"""
    global INDICATORS_METADATA_CACHE
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT type, output_fields FROM indicators")
        for row in cursor.fetchall():
            INDICATORS_METADATA_CACHE[row[0]] = json.loads(row[1])
```

---

### 2. 에러 처리

특정 필드 추출 실패 시 다른 필드는 계속 처리:

```python
try:
    indicator_values = []
    for i in range(start_idx, end_idx + 1):
        value = strategy_parser.indicator_calc.get_value(column_name, i)
        indicator_values.append(value)
    
    indicators_data[display_key] = indicator_values
except Exception as e:
    # 로그만 남기고 계속 진행
    logger.warning(f"지표 {display_key} (컬럼: {column_name}) 값 추출 실패: {e}")
```

---

### 3. 하위 호환성

기존 단일 출력 지표는 동일하게 작동:

```python
# EMA (단일 출력)
output_fields = ["main"]
column_name = "ema_1"
display_key = "ema_1"

# 기존 프론트엔드 코드와 호환
indicators_data["ema_1"] = [...]
```

---

## 🎉 완료!

**문제**: 차트 데이터 API에서 다중 출력 커스텀 지표를 지원하지 않음

**해결**:
1. ✅ 지표 메타 정보 로드 (output_fields)
2. ✅ 각 출력 필드별 데이터 추출
3. ✅ 점(.) 구분자로 통일된 키 형식
4. ✅ 에러 처리 강화

**효과**:
- ✅ 다중 출력 커스텀 지표 차트 표시 가능
- ✅ 프론트엔드와 일관된 키 형식
- ✅ 단일/다중 출력 모두 지원
- ✅ 에러 발생 시 부분 데이터라도 표시

---

**작성 일자**: 2025-12-13  
**수정 파일**: 1개 (`apps/api/routers/runs.py`)  
**상태**: 완료 ✅

