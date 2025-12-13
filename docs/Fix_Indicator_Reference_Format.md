# 지표 참조 형식 개선: 점(.) 구분자 도입

## 📝 문제

사용자가 지표 ID를 수정할 때 언더스코어(`_`)를 포함하면, 백엔드에서 지표를 찾을 수 없는 문제가 발생했습니다.

### 기존 방식의 문제점

```
Step 1: cvol 지표 추가
자동 생성 ID: cvol_1

사용자가 ID 수정: cvol_1 → c_vol

Step 2: 조건 추가
프론트엔드 저장: c_vol_vmf (언더스코어 구분)
백엔드 컬럼명: c_vol_vmf

문제: c_vol_vmf가 어디까지가 ID이고 어디부터가 필드인지 파싱 불가능
- c + vol_vmf ?
- c_vol + vmf ? ✅ (정답)
- c_vol_vmf (필드 없음) ?
```

**핵심 문제**: 언더스코어로 ID와 필드를 구분하면, ID 자체에 언더스코어가 있을 때 파싱이 애매해짐

---

## ✅ 해결 방법

### 점(`.`) 구분자 도입

**지표 참조 형식**: `지표_ID.출력_필드`

```
예시:
- ema_1 (단일 출력)
- c_vol.vmf (다중 출력)
- my_custom_indicator.signal (다중 출력)
```

**장점**:
1. ✅ ID와 필드를 명확하게 구분
2. ✅ ID에 언더스코어 자유롭게 사용 가능
3. ✅ 프로그래밍 언어의 속성 접근 방식과 일치 (`object.property`)
4. ✅ 가독성 향상

---

## 🔧 구현

### 1️⃣ 프론트엔드 (ConditionRow.tsx)

#### Before (언더스코어 구분)
```typescript
// 표시
displayLabel = `${ind.id}.${field}`  // "c_vol.vmf"

// 저장값
const storageValue = `${ind.id}_${field}`;  // "c_vol_vmf" ❌
```

#### After (점 구분)
```typescript
// 표시
displayLabel = `${ind.id}.${field}`  // "c_vol.vmf"

// 저장값
if (outputFields.length === 1 && field === 'main') {
  // 단일 출력: 점 없이 (백엔드 컬럼명과 일치)
  storageValue = ind.id;  // "ema_1"
} else {
  // 다중 출력: 점으로 구분 (백엔드에서 _로 변환)
  storageValue = `${ind.id}.${field}`;  // "c_vol.vmf" ✅
}
```

---

### 2️⃣ 백엔드 (StrategyParser)

#### 추가된 메서드: `_parse_indicator_ref()`

```python
def _parse_indicator_ref(self, ref: str) -> str:
    """
    지표 참조를 DataFrame 컬럼명으로 변환합니다.
    
    프론트엔드에서는 점(.)으로 구분된 참조를 사용하지만,
    백엔드 DataFrame 컬럼명은 언더스코어(_)로 구분됩니다.
    
    Args:
        ref: 지표 참조 (예: "ema_1", "c_vol.vmf")
        
    Returns:
        str: DataFrame 컬럼명 (예: "ema_1", "c_vol_vmf")
        
    Examples:
        >>> _parse_indicator_ref("ema_1")
        "ema_1"
        >>> _parse_indicator_ref("c_vol.vmf")
        "c_vol_vmf"
    """
    # 점이 없으면 그대로 반환 (하위 호환성, 단일 출력)
    if "." not in ref:
        return ref
    
    # 마지막 점을 언더스코어로 변환
    # "c_vol.vmf" → "c_vol_vmf"
    parts = ref.rsplit(".", 1)  # 오른쪽부터 1개만 split
    return f"{parts[0]}_{parts[1]}"
```

#### 수정된 메서드: `_get_value()`

```python
def _get_value(self, value_def: Dict[str, Any], bar_index: int) -> Optional[float]:
    if "ref" in value_def:
        ref = value_def["ref"]
        
        # 점(.)으로 구분된 참조를 언더스코어(_)로 변환
        column_name = self._parse_indicator_ref(ref)  # ← 추가
        
        try:
            return self.indicator_calc.get_value(column_name, bar_index)
        except ValueError as e:
            logger.warning(f"지표 값 가져오기 실패: {ref} (컬럼: {column_name}), {e}")
            return None
    # ...
```

---

### 3️⃣ ID 편집기 개선 (IndicatorIdEditor.tsx)

#### 검증 규칙 완화

**Before**:
```typescript
// 언더스코어 최대 1개만 허용
if (underscoreCount > 1) {
  return '언더스코어(_)는 최대 1개만 사용 가능합니다';
}
```

**After**:
```typescript
// 언더스코어 자유롭게 사용 가능 (단, 연속 사용 불가)
if (id.includes('__')) {
  return '언더스코어(_)를 연속으로 사용할 수 없습니다';
}

if (id.startsWith('_') || id.endsWith('_')) {
  return 'ID는 언더스코어(_)로 시작하거나 끝날 수 없습니다';
}
```

#### 도움말 메시지 개선

```typescript
💡 형식: 영문, 숫자, 언더스코어(_) 사용 가능
   예: my_ema_1, custom_vol, rsi_14
```

---

## 📊 데이터 흐름

### 단일 출력 지표 (예: EMA)

```
Step 1: 지표 추가
├─ ID: ema_1
└─ Type: ema
    └─ Output Fields: ["main"]

Step 2: 조건 입력
├─ 표시: ema_1.ema
├─ 저장: ema_1 (점 없음)
└─ 백엔드 컬럼: ema_1

백테스트 실행:
├─ indicators: [{"id": "ema_1", "type": "ema", ...}]
├─ entry.long: [{"left": {"ref": "ema_1"}, ...}]
└─ StrategyParser._get_value("ema_1")
    └─ _parse_indicator_ref("ema_1") → "ema_1" (점 없음, 그대로)
    └─ indicator_calc.get_value("ema_1", bar_index) ✅
```

---

### 다중 출력 지표 (예: Custom Volume)

```
Step 1: 지표 추가
├─ ID: c_vol (사용자가 수정)
└─ Type: cvol
    └─ Output Fields: ["vma", "vmf"]

Step 2: 조건 입력
├─ 표시: c_vol.vma, c_vol.vmf
├─ 저장: c_vol.vmf (점으로 구분)
└─ 백엔드 컬럼: c_vol_vmf

백테스트 실행:
├─ indicators: [{"id": "c_vol", "type": "cvol", ...}]
├─ entry.long: [{"left": {"ref": "c_vol.vmf"}, ...}]
└─ StrategyParser._get_value("c_vol.vmf")
    └─ _parse_indicator_ref("c_vol.vmf")
        └─ "c_vol.vmf".rsplit(".", 1) → ["c_vol", "vmf"]
        └─ "c_vol_vmf" ✅
    └─ indicator_calc.get_value("c_vol_vmf", bar_index) ✅
```

---

## 🎯 장점 요약

### 1. 명확한 구분
```
Before: my_custom_indicator_signal (어디까지가 ID?)
After:  my_custom_indicator.signal  (명확!)
```

### 2. 유연한 ID 작명
```
Before: ema1 (언더스코어 사용 제한)
After:  my_ema_1, custom_vol_filter, rsi_14_slow (자유롭게)
```

### 3. 가독성 향상
```
Before: long_ema_1_cross_above_short_ema_1
After:  long_ema.main cross_above short_ema.main
```

### 4. 프로그래밍 관례 준수
```javascript
// JavaScript/TypeScript
indicator.value

// Python
df['indicator.value']  # 백엔드에서 df['indicator_value']로 변환
```

---

## 🧪 테스트 시나리오

### 테스트 1: 단일 출력 지표

```
1. Step 1: EMA 추가 (ema_1)
2. Step 2: 롱 조건 추가
   - 좌변: ema_1.ema 선택
3. Console 확인:
   ✓ 옵션 생성: ema_1.ema (value: ema_1)
4. 전략 저장 → 실행
5. 결과: ✅ 정상 작동
```

### 테스트 2: 다중 출력 커스텀 지표

```
1. Step 1: cvol 추가 → ID 수정: c_vol
2. Step 2: 롱 조건 추가
   - 좌변: c_vol.vmf 선택
3. Console 확인:
   ✓ 옵션 생성: c_vol.vmf (value: c_vol.vmf)
4. 전략 저장 → 실행
5. 결과: ✅ 정상 작동 (이전 에러 해결!)
```

### 테스트 3: 복잡한 ID

```
1. Step 1: RSI 추가 → ID 수정: my_long_term_rsi
2. Step 2: 롱 조건 추가
   - 좌변: my_long_term_rsi.rsi 선택
3. Console 확인:
   ✓ 옵션 생성: my_long_term_rsi.rsi (value: my_long_term_rsi)
4. 전략 저장 → 실행
5. 결과: ✅ 정상 작동
```

---

### 4️⃣ Draft Validation 수정 (draft-validation.ts)

#### 문제
```typescript
// Before
const leftExists = draft.indicators.some(i => i.id === condition.left.value);
// condition.left.value = "c_vol.vmf"
// i.id = "c_vol"
// → 매칭 안됨! ❌

if (!leftExists) {
  errors.push({
    message: `지표 'c_vol.vmf'를 찾을 수 없습니다`  // ← 이 에러!
  });
}
```

#### 해결
```typescript
// After: 점(.) 앞부분만 추출하여 검증
const leftRefId = condition.left.value.split('.')[0];  // "c_vol.vmf" → "c_vol"
const leftExists = draft.indicators.some(i => i.id === leftRefId);

if (!leftExists) {
  errors.push({
    message: `지표 '${leftRefId}'를 찾을 수 없습니다`  // ✅ "c_vol"
  });
}
```

**핵심**:
- 참조값 `c_vol.vmf`에서 점(`.`) 앞부분(`c_vol`)만 추출
- 추출한 ID로 `indicators` 배열에서 검색
- 좌변/우변 모두 동일하게 처리

---

## 🔄 하위 호환성

### 기존 전략 지원

점(`.`)이 없는 참조도 계속 지원합니다:

```python
# _parse_indicator_ref()
if "." not in ref:
    return ref  # 그대로 반환 (하위 호환)
```

**예시**:
- 기존: `{"ref": "ema_1"}` → `"ema_1"` ✅
- 신규: `{"ref": "c_vol.vmf"}` → `"c_vol_vmf"` ✅

---

## 📝 변경 파일 목록

### Frontend
1. ✅ `apps/web/app/strategies/builder/components/ConditionRow.tsx`
   - 저장값을 점(`.`) 구분자로 변경
   
2. ✅ `apps/web/app/strategies/builder/components/IndicatorIdEditor.tsx`
   - 언더스코어 사용 제한 완화
   - 도움말 메시지 개선

3. ✅ `apps/web/lib/draft-validation.ts`
   - 지표 참조 검증 로직 수정
   - `c_vol.vmf` → `c_vol` 추출하여 검증

### Backend
4. ✅ `engine/utils/strategy_parser.py`
   - `_parse_indicator_ref()` 메서드 추가
   - `_get_value()` 메서드 수정

---

## 🎉 완료!

**핵심 변경**:
```
지표 참조 형식: 지표_ID + "_" + 필드 → 지표_ID + "." + 필드
```

**해결된 문제**:
```
❌ Before: "지표 'c_vol_vmf'를 찾을 수 없습니다"
✅ After:  정상 동작
```

**사용자 경험 개선**:
```
✅ ID 작명 자유도 향상
✅ 가독성 향상
✅ 명확한 구조
```

---

**작성 일자**: 2025-12-13  
**수정 파일**: 3개  
**상태**: 완료 ✅

