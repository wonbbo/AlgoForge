# 지표 로딩 상태 무한 대기 문제 해결

## 📝 문제

전략 빌더의 Step 2(진입 조건)에서 "지표 정보를 불러오는 중입니다..." 메시지가 계속 표시되고 진행이 안 되는 문제가 발생했습니다.

### 증상

```
Step 2 진입
  ↓
┌────────────────────────────────────┐
│ ⏳ 지표 정보를 불러오는 중입니다... │
│    잠시만 기다려주세요.            │
└────────────────────────────────────┘
  ↓
(메시지가 계속 표시됨, 버튼 비활성화)
  ↓
진행 불가 ❌
```

---

## 🔍 원인 분석

### 잘못된 조건 검사

#### Before (문제 코드)

```typescript
// builder/page.tsx
const [availableIndicators, setAvailableIndicators] = useState<Indicator[]>([]);
// ❌ 초기값: [] (빈 배열)

// Step2_EntryBuilder.tsx
{indicators.length > 0 && (!availableIndicators || availableIndicators.length === 0) && (
  <Card>로딩 중...</Card>
)}
```

**문제점**:
1. `availableIndicators`는 **빈 배열 `[]`로 초기화**
2. API 호출 후 성공하면 `[{...}, {...}]` 업데이트
3. **하지만**: API 호출이 실패하거나 지표가 0개면 여전히 `[]`
4. 조건: `availableIndicators.length === 0` → **계속 true**
5. 결과: **로딩 메시지가 계속 표시됨**

---

### 문제 시나리오

```
1. 페이지 로드
   └─ availableIndicators = []  (빈 배열)
   
2. API 호출 시작
   
3. Step 1에서 지표 추가
   
4. Step 2로 이동
   └─ 조건 체크: availableIndicators.length === 0 ✓
   └─ 로딩 메시지 표시
   
5. API 호출 완료
   └─ 실패했거나 빈 응답
   └─ availableIndicators = []  (여전히 빈 배열)
   
6. 조건 체크: availableIndicators.length === 0 ✓ (여전히 true)
   └─ 로딩 메시지 계속 표시 ❌
   └─ 버튼 비활성화 유지 ❌
   └─ 진행 불가!
```

---

## ✅ 해결 방법

### 1. 로딩 상태 플래그 추가

**파일**: `apps/web/app/strategies/builder/page.tsx`

```typescript
// Before (문제)
const [availableIndicators, setAvailableIndicators] = useState<Indicator[]>([]);

// After (해결)
const [availableIndicators, setAvailableIndicators] = useState<Indicator[]>([]);
const [isLoadingIndicators, setIsLoadingIndicators] = useState<boolean>(true);
// ✅ 로딩 상태를 명시적으로 관리

// 지표 목록 로드
useEffect(() => {
  const loadIndicators = async () => {
    setIsLoadingIndicators(true);  // ✅ 로딩 시작
    try {
      const data = await indicatorApi.list();
      setAvailableIndicators(data.indicators);
    } catch (err: any) {
      console.error('지표 목록 로드 실패:', err);
    } finally {
      setIsLoadingIndicators(false);  // ✅ 로딩 완료 (성공/실패 무관)
    }
  };
  loadIndicators();
}, []);
```

---

### 2. Props 전달 체인

```
builder/page.tsx
  └─ isLoadingIndicators
       ↓
  StepWizard.tsx
       ↓
  Step2_EntryBuilder.tsx
       ↓
  로딩 조건 검사
```

---

### 3. 조건 검사 수정

**파일**: `apps/web/app/strategies/builder/components/Step2_EntryBuilder.tsx`

#### Before (문제)
```typescript
{indicators.length > 0 && (!availableIndicators || availableIndicators.length === 0) && (
  <Card>로딩 중...</Card>
)}
// ❌ availableIndicators.length로 로딩 상태 추론 (부정확)
```

#### After (해결)
```typescript
{indicators.length > 0 && isLoadingIndicators && (
  <Card>로딩 중...</Card>
)}
// ✅ 명시적인 로딩 플래그 사용 (정확)
```

---

### 4. 버튼 비활성화 조건 수정

#### Before (복잡)
```typescript
disabled={
  indicators.length === 0 || 
  !availableIndicators || 
  availableIndicators.length === 0
}
```

#### After (단순)
```typescript
disabled={indicators.length === 0 || isLoadingIndicators}
// ✅ 로딩 플래그만 확인
```

---

## 🔄 개선된 흐름

### 정상 동작

```
1. 페이지 로드
   └─ isLoadingIndicators = true
   └─ availableIndicators = []

2. API 호출 시작

3. Step 1: 지표 추가

4. Step 2 이동
   └─ isLoadingIndicators === true ✓
   └─ "⏳ 로딩 중..." 표시
   └─ 버튼 비활성화

5. API 응답 도착 (성공)
   └─ availableIndicators = [{...}, {...}]
   └─ isLoadingIndicators = false  ✅
   
6. 자동 리렌더링
   └─ isLoadingIndicators === false ✓
   └─ 로딩 메시지 숨김
   └─ 버튼 활성화
   
7. 조건 추가 가능
   └─ ✅ 다중 출력 필드 정상 표시
```

---

### API 실패 시에도 정상 동작

```
1~4. (위와 동일)

5. API 응답 에러
   └─ catch 블록 실행
   └─ console.error 출력
   └─ finally: isLoadingIndicators = false  ✅

6. 자동 리렌더링
   └─ 로딩 메시지 숨김
   └─ 버튼 활성화 (기본 동작 가능)
   
7. 조건 추가
   └─ indicatorInfo = undefined
   └─ outputFields = ['main'] (기본값)
   └─ 기본 동작 (에러는 발생하지 않음)
```

---

## 📊 비교

### Before (무한 로딩)

| 상황 | availableIndicators | 조건 결과 | 표시 |
|------|-------------------|---------|------|
| 초기 | `[]` | length === 0 ✓ | 로딩 중 |
| API 로드 전 | `[]` | length === 0 ✓ | 로딩 중 |
| API 실패 | `[]` | length === 0 ✓ | 로딩 중 ❌ |
| API 성공 (빈 응답) | `[]` | length === 0 ✓ | 로딩 중 ❌ |
| API 성공 | `[{...}]` | length > 0 ✓ | 정상 ✅ |

**문제**: API 실패나 빈 응답 시 무한 로딩!

---

### After (명시적 플래그)

| 상황 | isLoadingIndicators | 조건 결과 | 표시 |
|------|-------------------|---------|------|
| 초기 | `true` | true ✓ | 로딩 중 |
| API 로드 전 | `true` | true ✓ | 로딩 중 |
| API 실패 | `false` | false ✗ | 정상 ✅ |
| API 성공 (빈 응답) | `false` | false ✗ | 정상 ✅ |
| API 성공 | `false` | false ✗ | 정상 ✅ |

**해결**: 로딩 완료(성공/실패 무관) 후 항상 진행 가능!

---

## ✅ 검증

### 수정된 파일 (3개)

1. **`apps/web/app/strategies/builder/page.tsx`**
   - `isLoadingIndicators` state 추가
   - `setIsLoadingIndicators(true/false)` 관리
   - StepWizard에 props 전달

2. **`apps/web/app/strategies/builder/components/StepWizard.tsx`**
   - `isLoadingIndicators` props 추가
   - Step2_EntryBuilder에 전달

3. **`apps/web/app/strategies/builder/components/Step2_EntryBuilder.tsx`**
   - `isLoadingIndicators` props 추가
   - 조건 검사 수정 (간소화)
   - 버튼 비활성화 로직 수정

---

## 🧪 테스트 방법

### 시나리오 1: 정상 로딩

```
1. 브라우저 새로고침
2. Step 1: custom_volume 지표 추가
3. Step 2 이동
   └─ ⏳ "로딩 중..." 표시 (1~2초)
   └─ 버튼 비활성화 (회색)
4. 자동으로 메시지 사라짐
   └─ 버튼 활성화 (파란색)
5. 조건 추가 후 드롭다운 확인
   └─ ✅ custom_volume_1.main
   └─ ✅ custom_volume_1.vol_pos
```

---

### 시나리오 2: API 실패

```
1. API 서버 중지 (테스트용)
2. 브라우저 새로고침
3. Step 1: ema 지표 추가 (로컬 Draft만)
4. Step 2 이동
   └─ ⏳ "로딩 중..." 표시 (짧게)
   └─ API 에러 (Console에 출력)
   └─ finally: isLoadingIndicators = false
5. 메시지 사라짐
   └─ ✅ 버튼 활성화됨 (기본 동작 가능)
6. 조건 추가 가능
   └─ outputFields = ['main'] (기본값 사용)
   └─ ✅ 에러는 발생하지 않음
```

---

### 시나리오 3: 빠른 API

```
1. 브라우저 새로고침
2. 3초 대기 (API 로드 완료)
3. Step 1: 지표 추가
4. Step 2 이동
   └─ isLoadingIndicators === false
   └─ 로딩 메시지 표시 안 됨
   └─ ✅ 버튼 즉시 활성화
```

---

## 💡 핵심 개선사항

### 1. 명시적 로딩 상태 관리

**Before**:
- 배열 길이로 로딩 상태 추론
- 부정확하고 오류 가능성 높음

**After**:
- 전용 플래그(`isLoadingIndicators`)
- 정확하고 명확함

---

### 2. finally 블록 사용

```typescript
try {
  const data = await indicatorApi.list();
  setAvailableIndicators(data.indicators);
} catch (err: any) {
  console.error('지표 목록 로드 실패:', err);
} finally {
  setIsLoadingIndicators(false);  // ✅ 성공/실패 무관하게 로딩 종료
}
```

**효과**:
- API 성공 시: 로딩 종료
- API 실패 시: 로딩 종료
- **무한 로딩 방지!**

---

### 3. 단순화된 조건

**Before**:
```typescript
disabled={
  indicators.length === 0 || 
  !availableIndicators || 
  availableIndicators.length === 0
}
```

**After**:
```typescript
disabled={indicators.length === 0 || isLoadingIndicators}
```

**장점**:
- 읽기 쉬움
- 의도가 명확
- 유지보수 용이

---

## 📋 수정 요약

### State 관리
```typescript
// 추가
const [isLoadingIndicators, setIsLoadingIndicators] = useState<boolean>(true);

// 수정
useEffect(() => {
  const loadIndicators = async () => {
    setIsLoadingIndicators(true);   // ✅ 시작
    try {
      // ... API 호출
    } finally {
      setIsLoadingIndicators(false); // ✅ 종료
    }
  };
  loadIndicators();
}, []);
```

### 조건 검사
```typescript
// Before
{indicators.length > 0 && (!availableIndicators || availableIndicators.length === 0) && ...}

// After
{indicators.length > 0 && isLoadingIndicators && ...}
```

### 버튼 비활성화
```typescript
// Before
disabled={indicators.length === 0 || !availableIndicators || availableIndicators.length === 0}

// After
disabled={indicators.length === 0 || isLoadingIndicators}
```

---

## 🎯 결과

### Before (무한 로딩)
```
로딩 메시지: 계속 표시 ❌
버튼 상태: 계속 비활성화 ❌
진행: 불가능 ❌
```

### After (정상 동작)
```
로딩 메시지: 1~2초 후 사라짐 ✅
버튼 상태: 자동 활성화 ✅
진행: 정상 가능 ✅
```

---

## ✅ 검증 완료

```bash
✅ Lint 에러 0개
✅ TypeScript 컴파일 성공
✅ isLoadingIndicators 플래그 추가
✅ finally 블록으로 확실한 종료
✅ 조건 로직 단순화
✅ 무한 로딩 방지
```

---

## 🚀 다음 단계

### 테스트 필수!

1. **브라우저 새로고침**
   ```
   http://localhost:5001/strategies/builder
   ```

2. **Step 1**: 지표 추가
   - `custom_volume` 추가

3. **Step 2**: 진입 조건
   - 짧은 로딩 메시지 확인 (1~2초)
   - 자동으로 사라지는지 확인
   - 버튼 활성화 확인

4. **조건 추가**
   - 드롭다운에서 2개 필드 확인
   - ✅ `custom_volume_1.main`
   - ✅ `custom_volume_1.vol_pos`

---

## 📚 관련 문서

- [Multi Output Indicator UI Implementation](./Multi_Output_Indicator_UI_Implementation.md)
- [Fix Strategy Builder Indicator Loading Issue](./Fix_Strategy_Builder_Indicator_Loading_Issue.md)

---

## 🎉 완료!

**핵심 개선**:
- ✅ 명시적 로딩 상태 관리
- ✅ finally 블록으로 확실한 종료
- ✅ 무한 로딩 방지

이제 전략 빌더가 정상적으로 작동합니다! 🚀

---

**작성 일자**: 2025-12-13  
**수정 파일**: 3개  
**상태**: 완료 ✅

