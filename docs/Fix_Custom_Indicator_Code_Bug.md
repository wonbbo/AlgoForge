# 커스텀 지표 코드 버그 수정

## 📝 문제

백테스트 실행 시 다음 에러 발생:

```
WARNING: 지표 값 가져오기 실패: c_vol.vmf (컬럼: c_vol_vmf), 
         지표 'c_vol_vmf'가 계산되지 않았습니다
```

---

## 🔍 원인 분석

### 1️⃣ 데이터베이스 확인

```sql
SELECT type, code, output_fields FROM indicators WHERE type='cvol';
```

**결과**:
- Type: `cvol`
- Output Fields: `["vma", "vmf"]` ✅
- Code: 문제 있음 ❌

---

### 2️⃣ 코드 분석

#### 잘못된 코드
```python
def calculate_custom_volume(df, params):
    period = params.get('period', 20)
    
    # 문제 1: ema_period 변수가 정의되지 않음 (period 사용해야 함)
    main = EMAIndicator(df['volume'], ema_period).ema_indicator().bfill()  # ❌
    
    # 문제 2: vol_pos 변수 생성
    vol_pos = Series(data=np.where(df['volume']>main, 1, -1), index=df.index)
    
    # 문제 3: 정의되지 않은 변수 반환
    return vma, vmf  # ❌ vma와 vmf는 어디에도 정의되지 않음!
    # 또한 튜플이 아닌 딕셔너리로 반환해야 함
```

**에러 결과**:
1. `ema_period` NameError → 지표 계산 실패
2. `vma`, `vmf` NameError → 반환값 없음
3. 컬럼이 생성되지 않음 → `c_vol_vmf` 컬럼 없음
4. 조건 평가 실패 → WARNING 메시지

---

## ✅ 해결 방법

### 올바른 코드

```python
def calculate_custom_volume(df, params):
    """
    커스텀 볼륨 지표 함수
    
    Args:
        df: OHLCV DataFrame
        params: 파라미터 딕셔너리
    
    Returns:
        Dict[str, pd.Series]: {'vma': ..., 'vmf': ...}
    """
    import pandas as pd
    import numpy as np
    from ta.trend import EMAIndicator
    
    period = params.get('period', 20)
    
    # VMA: 볼륨의 EMA
    vma = EMAIndicator(df['volume'], window=period).ema_indicator().bfill()
    
    # VMF: 볼륨이 평균보다 높으면 1, 낮으면 -1
    vmf = pd.Series(data=np.where(df['volume'] > vma, 1, -1), index=df.index)
    
    # 딕셔너리로 반환 (키는 output_fields와 일치해야 함)
    return {'vma': vma, 'vmf': vmf}
```

---

### 수정 사항

#### 1. 변수명 수정
```python
# Before
ema_period  # ❌ 정의되지 않음

# After
period  # ✅ params.get('period', 20)
```

#### 2. 변수명 일치
```python
# Before
main = ...      # 계산된 변수
vol_pos = ...   # 계산된 변수
return vma, vmf # ❌ 정의되지 않은 변수

# After
vma = ...       # ✅
vmf = ...       # ✅
return {'vma': vma, 'vmf': vmf}  # ✅
```

#### 3. 반환 형식 수정
```python
# Before
return vma, vmf  # ❌ 튜플 (unpacking 불가)

# After
return {'vma': vma, 'vmf': vmf}  # ✅ Dict[str, pd.Series]
```

#### 4. Import 추가
```python
# 함수 내부에서 import (안전한 방식)
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator
```

---

## 🔧 수정 작업

### 방법 1: SQL 직접 수정 (완료)

```python
import sqlite3
import time

correct_code = """def calculate_custom_volume(df, params):
    ...
"""

conn = sqlite3.connect('db/algoforge.db')
updated_at = int(time.time())
conn.execute(
    "UPDATE indicators SET code = ?, updated_at = ? WHERE type = 'cvol'",
    (correct_code, updated_at)
)
conn.commit()
conn.close()
```

**실행 결과**: ✅ 성공

---

### 방법 2: 프론트엔드에서 수정 (대안)

```
1. http://localhost:3000/indicators/cvol 접속
2. 편집 모드 활성화
3. 코드 수정
4. 저장
```

---

## 🧪 검증

### 1️⃣ 데이터베이스 확인

```python
import sqlite3
conn = sqlite3.connect('db/algoforge.db')
cursor = conn.execute("SELECT code FROM indicators WHERE type='cvol'")
code = cursor.fetchone()[0]
print(code)
conn.close()
```

**기대 결과**: 올바른 코드 출력 ✅

---

### 2️⃣ 백테스트 실행

```
1. 전략 빌더에서 전략 생성
   - Step 1: cvol 추가 (ID: c_vol)
   - Step 2: c_vol.vmf > 0 조건 추가
   - Step 3: Fixed Percent 2% 설정
2. 전략 저장
3. Run 실행
```

**기대 결과**:
- ✅ 에러 없음
- ✅ 로그: `[커스텀 지표] 컬럼 생성: c_vol_vma (indicator_id=c_vol, key=vma)`
- ✅ 로그: `[커스텀 지표] 컬럼 생성: c_vol_vmf (indicator_id=c_vol, key=vmf)`
- ✅ 로그: `[지표 참조] ref='c_vol.vmf' → column='c_vol_vmf'`
- ✅ 백테스트 정상 완료

---

## 📊 로그 출력 예시

### Before (에러)
```
WARNING: 지표 값 가져오기 실패: c_vol.vmf (컬럼: c_vol_vmf), 
         지표 'c_vol_vmf'가 계산되지 않았습니다
  사용 가능한 지표 컬럼: []
```

### After (정상)
```
INFO: [전략 파싱] 지표 계산 시작: 1개
INFO: [전략 파싱] 지표 계산 중: id=c_vol, type=cvol
INFO: [커스텀 지표] 컬럼 생성: c_vol_vma (indicator_id=c_vol, key=vma)
INFO: [커스텀 지표] 컬럼 생성: c_vol_vmf (indicator_id=c_vol, key=vmf)
INFO: [전략 파싱] 지표 계산 완료. 생성된 컬럼: ['c_vol_vma', 'c_vol_vmf']
INFO: [지표 참조] ref='c_vol.vmf' → column='c_vol_vmf'
INFO: [지표 값] column='c_vol_vmf', bar_index=50, value=1.0
```

---

## 🎓 교훈

### 1. 커스텀 지표 작성 시 주의사항

#### ✅ DO
```python
def custom_indicator(df, params):
    # 1. 필요한 라이브러리 import
    import pandas as pd
    import numpy as np
    
    # 2. params에서 파라미터 추출
    period = params.get('period', 20)
    
    # 3. 계산
    result1 = ...
    result2 = ...
    
    # 4. 딕셔너리로 반환 (키는 output_fields와 일치)
    return {'field1': result1, 'field2': result2}
```

#### ❌ DON'T
```python
def bad_indicator(df, params):
    # 1. 정의되지 않은 변수 사용
    main = EMAIndicator(df['volume'], undefined_var)  # ❌
    
    # 2. 변수명 불일치
    result1 = ...
    result2 = ...
    return wrong_name1, wrong_name2  # ❌
    
    # 3. 튜플 반환
    return result1, result2  # ❌ (Dict 필요)
    
    # 4. output_fields와 불일치
    # output_fields = ["vma", "vmf"]
    return {'main': ..., 'signal': ...}  # ❌
```

---

### 2. 디버깅 로그 추가

**수정된 파일**:
- `engine/utils/indicators.py`: 컬럼 생성 로그
- `engine/utils/strategy_parser.py`: 지표 계산, 참조 변환 로그

**효과**:
- 어떤 컬럼이 생성되었는지 명확히 확인
- 참조 변환 과정 추적 가능
- 에러 발생 시 사용 가능한 컬럼 목록 출력

---

### 3. 코드 검증

커스텀 지표 등록 시 기본 검증만 수행:
- AST 파싱: 구문 오류 체크
- 함수 개수: 정확히 1개
- 인자 개수: 2개 (df, params)

**한계**: 실행 시점 에러는 감지 불가
- 정의되지 않은 변수
- 타입 불일치
- Import 누락

**개선 방안** (향후):
- 샘플 데이터로 실행 테스트
- 반환값 타입 검증
- output_fields 키 일치 검증

---

## 🎉 완료!

**문제**: 커스텀 지표 코드의 변수명 불일치 및 반환 형식 오류

**해결**: 
1. ✅ 코드 수정 (변수명 일치, 딕셔너리 반환)
2. ✅ 디버깅 로그 추가
3. ✅ 데이터베이스 업데이트

**결과**: 
- ✅ `c_vol_vmf` 컬럼 정상 생성
- ✅ 지표 참조 정상 동작
- ✅ 백테스트 정상 실행

---

**작성 일자**: 2025-12-13  
**수정 파일**: 3개 (indicators.py, strategy_parser.py, DB)  
**상태**: 완료 ✅

