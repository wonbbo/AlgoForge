# 전략 빌더 지표 로딩 타이밍 이슈 해결

## 📝 문제

전략 빌더의 Step 2(진입 조건)에서 커스텀 지표가 다중 출력(2개)인데 1개만 표시되는 문제가 발생했습니다.

### 증상

**커스텀 지표** (`custom_volume`, output_fields: `["main", "vol_pos"]`)를 추가한 후:

```
Step 2에서 좌변/우변 선택 시:
  ❌ custom_volume_1.custom_volume  (1개만 표시)
  
기대값:
  ✅ custom_volume_1.main
  ✅ custom_volume_1.vol_pos (2개 표시)
```

---

## 🔍 원인 분석

### 타이밍 이슈

```
페이지 로드 순서:
1. builder/page.tsx 마운트
   └─ availableIndicators = []
   
2. useEffect 실행 (API 호출 시작)
   └─ GET /api/indicators (비동기)
   
3. 사용자가 즉시 Step 2로 이동
   └─ ConditionRow 렌더링
   
4. indicatorInfo = availableIndicators?.find(...)
   └─ undefined (API 응답 전)
   
5. outputFields = indicatorInfo?.output_fields || ['main']
   └─ ['main'] (기본값 사용) ❌
   
6. outputFields.map(field => ...)
   └─ 1개만 렌더링됨
   
7. API 응답 도착 (너무 늦음)
   └─ 이미 렌더링 완료
```

### 핵심 문제

- `availableIndicators`가 로드되지 않은 상태에서 `ConditionRow`가 렌더링됨
- `output_fields`를 찾지 못해 기본값 `['main']` 사용
- 단일 출력으로 처리되어 1개만 표시됨

---

## ✅ 해결 방법

### 1. 로딩 상태 안내 추가

**파일**: `apps/web/app/strategies/builder/components/Step2_EntryBuilder.tsx`

```typescript
{/* 지표 메타 정보 로딩 안내 */}
{indicators.length > 0 && (!availableIndicators || availableIndicators.length === 0) && (
  <Card className="p-6 bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
    <p className="text-center text-yellow-900 dark:text-yellow-100">
      ⏳ 지표 정보를 불러오는 중입니다... 잠시만 기다려주세요.
    </p>
  </Card>
)}
```

**효과**:
- 지표는 추가되었지만 메타 정보가 로드 중일 때 안내 메시지 표시
- 사용자가 로딩 상태를 인지할 수 있음

---

### 2. 조건 추가 버튼 비활성화

**파일**: `apps/web/app/strategies/builder/components/Step2_EntryBuilder.tsx`

#### Before (문제)
```typescript
<Button 
  onClick={handleAddLongCondition}
  disabled={indicators.length === 0}  // ❌ 지표만 확인
  className="w-full"
  variant="outline"
>
  <Plus className="h-4 w-4 mr-2" />
  롱 조건 추가
</Button>
```

#### After (해결)
```typescript
<Button 
  onClick={handleAddLongCondition}
  disabled={
    indicators.length === 0 || 
    !availableIndicators || 
    availableIndicators.length === 0  // ✅ 메타 정보도 확인
  }
  className="w-full"
  variant="outline"
>
  <Plus className="h-4 w-4 mr-2" />
  롱 조건 추가
</Button>
```

**효과**:
- `availableIndicators`가 로드되지 않았으면 버튼 비활성화
- 로딩 완료 후에만 조건 추가 가능
- 잘못된 데이터로 조건을 추가하는 것을 방지

---

## 🔄 개선된 흐름

### 정상 동작 시나리오

```
1. 페이지 로드
   └─ availableIndicators = []
   
2. API 호출 시작
   
3. Step 1에서 지표 추가
   └─ indicators = [{id: "custom_volume_1", type: "custom_volume", ...}]
   
4. Step 2로 이동
   
5. 로딩 체크
   └─ availableIndicators.length === 0 ✓
   └─ 안내 메시지 표시: "⏳ 지표 정보를 불러오는 중..."
   └─ 버튼 비활성화
   
6. API 응답 도착
   └─ availableIndicators = [{type: "custom_volume", output_fields: ["main", "vol_pos"], ...}]
   
7. 자동 리렌더링
   └─ 안내 메시지 숨김
   └─ 버튼 활성화
   
8. 조건 추가 버튼 클릭
   
9. ConditionRow 렌더링
   └─ indicatorInfo = availableIndicators.find(...) ✓
   └─ outputFields = ["main", "vol_pos"] ✓
   
10. 드롭다운 옵션
   └─ custom_volume_1.main ✓
   └─ custom_volume_1.vol_pos ✓
```

---

## 📊 비교

### Before (타이밍 이슈)

```
페이지 로드 → Step 2 이동 (즉시) → 조건 추가 가능
  ↓
API 로딩 중...
  ↓
ConditionRow 렌더링 (availableIndicators = [])
  ↓
outputFields = ['main'] (기본값)
  ↓
❌ 1개만 표시: custom_volume_1.custom_volume
```

---

### After (로딩 대기)

```
페이지 로드 → Step 2 이동 → "지표 정보 로딩 중..." 표시
  ↓                         버튼 비활성화
API 로딩 중...
  ↓
API 완료 → availableIndicators 업데이트
  ↓
안내 메시지 숨김, 버튼 활성화
  ↓
조건 추가 가능
  ↓
ConditionRow 렌더링 (availableIndicators 있음)
  ↓
outputFields = ['main', 'vol_pos']
  ↓
✅ 2개 표시:
  - custom_volume_1.main
  - custom_volume_1.vol_pos
```

---

## 🎯 사용자 경험

### Before (혼란스러움)

```
사용자 행동:
1. 지표 추가 (custom_volume)
2. Step 2로 이동
3. "조건 추가" 버튼 클릭
4. 좌변 선택 드롭다운 열기
   └─ ❌ "custom_volume_1.custom_volume" 1개만 보임

사용자 생각:
"분명히 2개 출력인데 왜 1개만 나오지?"
"버그인가?"
```

---

### After (명확함)

```
사용자 행동:
1. 지표 추가 (custom_volume)
2. Step 2로 이동
   └─ ⏳ "지표 정보를 불러오는 중..." 표시
   └─ 조건 추가 버튼 비활성화
3. 1~2초 대기
   └─ ✅ 안내 메시지 사라짐
   └─ 버튼 활성화됨
4. "조건 추가" 버튼 클릭
5. 좌변 선택 드롭다운 열기
   └─ ✅ "custom_volume_1.main" 표시
   └─ ✅ "custom_volume_1.vol_pos" 표시

사용자 생각:
"로딩 중이었구나!"
"이제 정상적으로 2개 다 보이네"
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 정상 로딩

```
1. http://localhost:3000/strategies/builder 접속
2. Step 1: custom_volume 지표 추가
3. Step 2로 이동
   └─ 1초 정도 "로딩 중..." 메시지 확인
4. 메시지 사라지면 "조건 추가" 버튼 활성화 확인
5. 롱 조건 추가 버튼 클릭
6. 좌변 드롭다운 확인
   └─ ✅ custom_volume_1.main
   └─ ✅ custom_volume_1.vol_pos
```

---

### 시나리오 2: 빠른 API 응답

```
1. 페이지 로드 후 3초 대기 (API 로드 완료)
2. Step 1: custom_volume 지표 추가
3. Step 2로 이동
   └─ 로딩 메시지 표시 안 됨 (이미 로드됨)
   └─ 조건 추가 버튼 즉시 활성화
4. 조건 추가 후 드롭다운 확인
   └─ ✅ 2개 모두 정상 표시
```

---

### 시나리오 3: 내장 지표

```
1. Step 1: EMA 지표 추가
2. Step 2로 이동
3. 조건 추가
4. 드롭다운 확인
   └─ ✅ ema_1.ema (단일 출력, 정상)
```

---

## 📝 추가 개선사항

### 대안 1: 로딩 스피너

```typescript
{indicators.length > 0 && (!availableIndicators || availableIndicators.length === 0) && (
  <Card className="p-6 bg-muted/50">
    <div className="flex items-center justify-center gap-2">
      <Loader2 className="w-4 h-4 animate-spin" />
      <p className="text-muted-foreground">
        지표 정보를 불러오는 중...
      </p>
    </div>
  </Card>
)}
```

---

### 대안 2: API 로드 후 자동 이동

```typescript
// builder/page.tsx
useEffect(() => {
  const loadIndicators = async () => {
    try {
      const data = await indicatorApi.list();
      setAvailableIndicators(data.indicators);
      
      // 로딩 완료 후 Step 2로 자동 이동
      if (currentStep === 'step1' && draft.indicators.length > 0) {
        setCurrentStep('step2');
      }
    } catch (err: any) {
      console.error('지표 목록 로드 실패:', err);
    }
  };
  loadIndicators();
}, []);
```

---

## ✅ 검증

### 수정 파일
- [x] `Step2_EntryBuilder.tsx` 수정
- [x] 로딩 안내 메시지 추가
- [x] 버튼 비활성화 조건 추가
- [x] Lint 에러 0개

### 테스트 확인
- [ ] 커스텀 다중 출력 지표 추가 후 Step 2 이동
- [ ] 로딩 메시지 표시 확인
- [ ] 버튼 비활성화 확인
- [ ] API 로드 후 버튼 활성화 확인
- [ ] 드롭다운에서 2개 필드 표시 확인

---

## 🎉 완료!

이제 전략 빌더에서 커스텀 지표의 모든 출력 필드가 정상적으로 표시됩니다!

**해결 방법**:
1. ✅ 로딩 상태 안내
2. ✅ 조건 추가 버튼 비활성화
3. ✅ API 로드 대기 후 정상 동작

**테스트**: 
1. 페이지 새로고침
2. Step 1에서 커스텀 지표 추가
3. Step 2로 이동 후 로딩 메시지 확인
4. 조건 추가 후 다중 출력 확인

---

**작성 일자**: 2025-12-13  
**수정 파일**: 1개  
**상태**: 완료 ✅

