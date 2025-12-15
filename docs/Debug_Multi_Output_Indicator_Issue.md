# 다중 출력 지표 표시 문제 디버깅

## 📝 현재 상황

전략 빌더의 진입 탭에서 커스텀 지표(2개 출력)를 추가했는데, 좌변/우변 드롭다운에 1개만 표시되는 문제가 발생하고 있습니다.

### 예상 동작
```
커스텀 지표 추가: custom_volume (output_fields: ["main", "vol_pos"])
  ↓
Step 2 진입 조건에서 보여야 할 옵션:
  ✅ custom_volume_1.main
  ✅ custom_volume_1.vol_pos
```

### 실제 동작
```
드롭다운에서 보이는 옵션:
  ❌ custom_volume_1.custom_volume (1개만)
```

---

## 🔍 디버깅 방법

### 1. 브라우저 개발자 도구 열기

```
브라우저에서 F12 키 또는
우클릭 → 검사 → Console 탭
```

---

### 2. 페이지 새로고침

```
http://localhost:5001/strategies/builder
```

**확인사항**: Console에 다음 로그가 출력되는지 확인

```javascript
[Builder] 지표 목록 로드 완료: 5 개
[Builder] 커스텀 지표: [
  {
    type: "custom_volume",
    output_fields: ["main", "vol_pos"]  // ✅ 2개 확인!
  }
]
```

**분석**:
- ✅ 2개 필드가 로드되면 → 프론트엔드 문제
- ❌ 1개만 로드되면 → 백엔드/DB 문제

---

### 3. Step 1에서 지표 추가

```
custom_volume 지표 "+" 버튼 클릭
```

---

### 4. Step 2로 이동 후 조건 추가

```
"롱 조건 추가" 버튼 클릭
```

---

### 5. 좌변 드롭다운 클릭

**Console 로그 확인**:

```javascript
[ConditionRow-좌변] custom_volume_1 (custom_volume) → outputFields: ["main", "vol_pos"]
  - 옵션: custom_volume_1.main (value: custom_volume_1)
  - 옵션: custom_volume_1.vol_pos (value: custom_volume_1_vol_pos)
```

**분석**:
- ✅ 2개 로그가 출력되면 → 렌더링은 정상 (브라우저 문제?)
- ❌ 1개만 출력되면 → `outputFields` 값 확인 필요

---

## 🧪 체크리스트

### 백엔드 확인

```bash
# 1. API 서버 실행 확인
curl http://localhost:6000/api/indicators/

# 2. custom_volume 지표 확인
curl http://localhost:6000/api/indicators/custom_volume
```

**응답 확인**:
```json
{
  "name": "CustomVolume",
  "type": "custom_volume",
  "output_fields": ["main", "vol_pos"],  // ✅ 2개 확인!
  ...
}
```

**만약 1개만 나오면**:
```bash
# DB 직접 확인 (Python 스크립트 작성)
```

---

### 프론트엔드 확인

#### 체크 1: API 응답
```javascript
// Console에서 실행
fetch('http://localhost:6000/api/indicators/')
  .then(r => r.json())
  .then(data => {
    const custom = data.indicators.find(i => i.type === 'custom_volume');
    console.log('custom_volume output_fields:', custom?.output_fields);
  });
```

**기대값**: `["main", "vol_pos"]`

---

#### 체크 2: State 확인
```javascript
// React DevTools 설치 후
// Components 탭 → StrategyBuilderPage 선택
// availableIndicators state 확인
```

---

#### 체크 3: 렌더링 확인
```
드롭다운을 열고 Console 로그 확인:

✅ 정상인 경우:
  [ConditionRow-좌변] custom_volume_1 (custom_volume) → outputFields: (2) ["main", "vol_pos"]
    - 옵션: custom_volume_1.main (value: custom_volume_1)
    - 옵션: custom_volume_1.vol_pos (value: custom_volume_1_vol_pos)

❌ 문제가 있는 경우:
  [ConditionRow-좌변] custom_volume_1 (custom_volume) → outputFields: ["main"]
    - 옵션: custom_volume_1.custom_volume (value: custom_volume_1)
```

---

## 🔧 가능한 원인과 해결책

### 원인 1: DB에 1개만 저장됨

**확인**:
```bash
cd /home/wonbbo/algoforge
python -m apps.api.db.check_indicators
```

**해결**: 지표 재등록 또는 DB 직접 수정

---

### 원인 2: API 응답에 output_fields가 문자열로 옴

**증상**: 
```json
{
  "output_fields": "[\"main\", \"vol_pos\"]"  // ❌ 문자열
}
```

**원인**: JSON 직렬화 문제

**해결**: `apps/api/routers/indicators.py` 확인
```python
# 현재 코드
output_fields=json.loads(row[8])  # ✅ JSON 파싱 (정상)

# 만약 문자열로 저장되어 있다면
output_fields=json.loads(json.loads(row[8]))  # 이중 파싱 필요
```

---

### 원인 3: 캐싱 문제

**해결**:
```bash
# 1. .next 폴더 삭제
cd apps\web
rd /s /q .next

# 2. 브라우저 캐시 삭제
Ctrl + Shift + Del → 캐시 삭제

# 3. 하드 리프레시
Ctrl + Shift + R
```

---

### 원인 4: 지표가 이전 버전으로 등록됨

**확인**: 지표 상세 페이지 접속
```
http://localhost:5001/indicators/custom_volume
```

**출력 필드** 섹션에서 실제 필드 확인

---

## 📊 예상 시나리오별 해결

### 시나리오 A: DB 문제

**Console 로그**:
```
[Builder] 커스텀 지표: [
  {
    type: "custom_volume",
    output_fields: ["main"]  // ❌ 1개만
  }
]
```

**해결**:
1. 지표 상세 페이지에서 편집
2. 출력 필드: `main, vol_pos` 입력
3. 저장

---

### 시나리오 B: API 파싱 문제

**Console 로그**:
```
[Builder] 커스텀 지표: [
  {
    type: "custom_volume",
    output_fields: "[\"main\", \"vol_pos\"]"  // ❌ 문자열
  }
]
```

**해결**: API 코드 수정 필요 (Agent 모드로 전환)

---

### 시나리오 C: 타이밍 문제

**Console 로그**:
```
[ConditionRow-좌변] custom_volume_1 (custom_volume) → outputFields: ["main"]
```

하지만 후속 로그에서:
```
[Builder] 커스텀 지표: [
  {
    type: "custom_volume",
    output_fields: ["main", "vol_pos"]  // ✅ 2개 (늦게 로드됨)
  }
]
```

**해결**: 이미 로딩 상태 관리로 해결됨 (최신 코드)

---

## 🎯 즉시 테스트 절차

### 1단계: 브라우저 콘솔 확인

```
1. F12 키 (개발자 도구)
2. Console 탭
3. 페이지 새로고침 (Ctrl + Shift + R)
4. 로그 확인:
   [Builder] 지표 목록 로드 완료: ? 개
   [Builder] 커스텀 지표: [...]
```

**여기서 output_fields를 확인하세요!**

---

### 2단계: 지표 추가 및 조건 설정

```
1. Step 1: custom_volume "+" 버튼
2. Step 2: "롱 조건 추가" 버튼
3. 좌변 드롭다운 클릭
4. Console 로그 확인:
   [ConditionRow-좌변] custom_volume_1 (custom_volume) → outputFields: [?]
```

**여기서 outputFields가 몇 개인지 확인하세요!**

---

### 3단계: 결과 리포트

**Console 로그를 복사해서 다음 형식으로 공유해주세요**:

```
[Builder] 지표 목록 로드 완료: X 개
[Builder] 커스텀 지표: [...]

[ConditionRow-좌변] custom_volume_1 (custom_volume) → outputFields: [...]
  - 옵션: ...
  - 옵션: ...
```

이 로그를 보면 정확한 원인을 파악할 수 있습니다!

---

## 🎉 다음 단계

로그를 확인한 후:

1. **output_fields가 2개로 로드됨** → 렌더링 문제 (추가 수정 필요)
2. **output_fields가 1개만 로드됨** → DB/API 문제 (재등록 또는 수정 필요)
3. **로그가 안 나옴** → API 호출 실패 (서버 확인 필요)

---

**작성 일자**: 2025-12-13  
**상태**: 디버깅 로그 추가 완료  
**다음**: 사용자 테스트 후 원인 파악

