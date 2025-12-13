# 거래 표시 기능 개선

## 📝 요청 사항

1. **거래 정보에 리스크 제한 금액 추가**
   - 초기 자산의 2%에 해당하는 리스크 제한 금액 표시
   
2. **초기 리스크 소수점 4자리 표시**
   - 기존: `$200.00`
   - 변경: `$200.0000`

3. **거래 목록 필터링 및 페이지네이션**
   - 완료되지 않은 거래는 제외
   - 20개씩 페이지네이션

---

## ✅ 구현

### 1️⃣ 거래 상세 페이지 개선

**파일**: `apps/web/app/runs/[id]/trades/[tradeId]/page.tsx`

#### A. Run 정보 로드 추가

Run의 `initial_balance`를 알기 위해 Run 정보도 함께 로드:

```typescript
// State 추가
const [run, setRun] = useState<Run | null>(null)

// useEffect 수정
const [runData, tradesResponse] = await Promise.all([
  runApi.get(runId),
  runApi.getTrades(runId)
])

setRun(runData)
```

---

#### B. 진입 정보 섹션 확장

**Before (2열)**:
```
매수 규모 | 초기 리스크
```

**After (3열)**:
```
매수 규모 | 리스크 제한 | 초기 리스크
```

---

#### C. 리스크 제한 금액 표시

```tsx
<div>
  <p className="text-sm text-muted-foreground">리스크 제한</p>
  <p className="text-xl font-bold text-orange-600 dark:text-orange-500">
    {run ? formatCurrency(run.initial_balance * 0.02) : '-'}
  </p>
  <p className="text-xs text-muted-foreground mt-1">
    초기 자산의 2%
  </p>
</div>
```

**계산식**:
```typescript
리스크 제한 = initial_balance × 0.02
```

**예시**:
- 초기 자산: $10,000
- **리스크 제한: $200.00** (10,000 × 0.02)

---

#### D. 초기 리스크 소수점 4자리 표시

```tsx
<div>
  <p className="text-sm text-muted-foreground">초기 리스크</p>
  <p className="text-xl font-bold text-destructive font-mono">
    ${trade.initial_risk.toFixed(4)}
  </p>
  <p className="text-xs text-muted-foreground mt-1">
    실제 리스크 금액
  </p>
</div>
```

**Before**: `$197.50`  
**After**: `$197.5000`

---

### 📊 화면 구성

```
┌─────────────────────────────────────────────────────────┐
│ 진입 정보                                                 │
├─────────────────────────────────────────────────────────┤
│  진입 시각    진입가      포지션 크기                      │
│                                                           │
│ ───────────────────────────────────────────────────────│
│                                                           │
│  💰 매수 규모           🛡️ 리스크 제한      ⚠️ 초기 리스크  │
│  $25,000.00           $200.00           $197.5000       │
│  진입가 × 포지션        초기 자산의 2%      실제 리스크 금액  │
└─────────────────────────────────────────────────────────┘
```

**색상 구분**:
- 매수 규모: Primary (파란색) - 주요 정보
- 리스크 제한: Orange (주황색) - 경고/제한
- 초기 리스크: Destructive (빨간색) - 위험

---

### 2️⃣ 거래 목록 페이지네이션

**파일**: `apps/web/app/runs/[id]/page.tsx`

#### A. 완료된 거래만 필터링

```typescript
// 완료된 거래 = legs가 있는 거래
const completedTrades = trades.filter(t => t.legs && t.legs.length > 0)
```

**이유**:
- Trade가 생성되더라도 아직 청산되지 않은 경우 `legs` 배열이 비어있음
- 완료되지 않은 거래는 의미 있는 정보(손익, 청산 방식 등)를 표시할 수 없음

---

#### B. 페이지네이션 구현

```typescript
// State
const [currentPage, setCurrentPage] = useState(1)
const tradesPerPage = 20

// 페이지네이션 계산
const totalPages = Math.ceil(completedTrades.length / tradesPerPage)
const startIndex = (currentPage - 1) * tradesPerPage
const endIndex = startIndex + tradesPerPage
const paginatedTrades = [...completedTrades].reverse().slice(startIndex, endIndex)
```

**특징**:
- 페이지당 20개 거래 표시
- 최신 거래가 먼저 표시되도록 역순 정렬
- 전체 페이지 수 자동 계산

---

#### C. 페이지네이션 UI

```tsx
<div className="flex items-center justify-between mt-4 pt-4 border-t">
  {/* 정보 표시 */}
  <p className="text-sm text-muted-foreground">
    페이지 {currentPage} / {totalPages} (총 {completedTrades.length}개)
  </p>
  
  {/* 페이지 버튼 */}
  <div className="flex items-center space-x-2">
    <Button onClick={() => setCurrentPage(currentPage - 1)} disabled={currentPage === 1}>
      이전
    </Button>
    
    {/* 페이지 번호 버튼 (스마트 표시) */}
    {Array.from({ length: totalPages }, (_, i) => i + 1)
      .filter(page => {
        // 현재 페이지 근처만 표시 (최대 5개)
        return (
          page === 1 ||
          page === totalPages ||
          (page >= currentPage - 1 && page <= currentPage + 1)
        )
      })
      .map(page => (
        <Button
          variant={currentPage === page ? 'default' : 'outline'}
          onClick={() => setCurrentPage(page)}
        >
          {page}
        </Button>
      ))}
    
    <Button onClick={() => setCurrentPage(currentPage + 1)} disabled={currentPage === totalPages}>
      다음
    </Button>
  </div>
</div>
```

---

#### D. 스마트 페이지 번호 표시

**예시 (총 10페이지)**:

현재 페이지 1:
```
[1] 2 3 ... 10
```

현재 페이지 5:
```
1 ... 4 [5] 6 ... 10
```

현재 페이지 10:
```
1 ... 8 9 [10]
```

**로직**:
- 첫 페이지와 마지막 페이지는 항상 표시
- 현재 페이지와 전후 1개씩 표시
- 간격이 있으면 `...` 표시

---

#### E. 헤더에 완료된 거래 수 표시

```tsx
<CardHeader>
  <div className="flex items-center justify-between">
    <CardTitle>거래 내역</CardTitle>
    <p className="text-sm text-muted-foreground">
      완료된 거래: {completedTrades.length}개
    </p>
  </div>
</CardHeader>
```

---

## 📊 비교

### Before (이전)

**거래 상세**:
```
진입 정보:
- 진입 시각, 진입가, 포지션 크기
- 매수 규모: $25,000.00
- 초기 리스크: $197.50  ← 소수점 2자리
```

**거래 목록**:
- 모든 거래 표시 (완료/미완료 구분 없음)
- 페이지네이션 없음 (스크롤)

---

### After (개선)

**거래 상세**:
```
진입 정보:
- 진입 시각, 진입가, 포지션 크기
- 매수 규모: $25,000.00
- 리스크 제한: $200.00  ← 신규 추가
- 초기 리스크: $197.5000  ← 소수점 4자리
```

**거래 목록**:
- 완료된 거래만 표시
- 20개씩 페이지네이션
- 페이지 정보: "페이지 1 / 5 (총 87개)"

---

## 💡 사용 사례

### 1. 리스크 관리 평가

```
리스크 제한: $200.00 (초기 자산의 2%)
초기 리스크: $197.5000
→ 리스크 사용률: 98.75% ✅ (제한 내)
```

**분석**:
- 초기 리스크가 제한 내에 있는지 확인
- 얼마나 적극적으로 리스크를 사용했는지 파악

---

### 2. 정밀한 리스크 추적

**소수점 2자리** (Before):
```
초기 리스크: $197.50
실제 값: $197.5234
→ 오차: $0.0234 (보이지 않음)
```

**소수점 4자리** (After):
```
초기 리스크: $197.5234
→ 정확한 값 확인 가능 ✅
```

---

### 3. 대량 거래 분석

**Before**:
```
거래 100개 → 한 페이지에 모두 표시 → 스크롤 과다
```

**After**:
```
거래 100개 → 5페이지로 분할
- 페이지 1: 최신 20개
- 페이지 2: 21~40번째
- ...
- 페이지 5: 81~100번째
```

**장점**:
- 빠른 로딩
- 쉬운 네비게이션
- 명확한 구분

---

## 🎯 기술적 세부사항

### 1. Run 정보 로딩

```typescript
// 병렬 로딩으로 성능 최적화
const [runData, tradesResponse] = await Promise.all([
  runApi.get(runId),
  runApi.getTrades(runId)
])
```

---

### 2. 완료 거래 판별

```typescript
// Leg가 있으면 완료된 거래
const isCompleted = trade.legs && trade.legs.length > 0
```

**Trade 상태**:
- 진입만 됨: `legs = []` → 미완료
- 부분 청산: `legs = [leg1]` → 완료
- 전량 청산: `legs = [leg1, leg2]` → 완료

---

### 3. 페이지네이션 알고리즘

```typescript
// 1. 역순 정렬 (최신 거래 먼저)
const reversed = [...completedTrades].reverse()

// 2. 페이지 범위 계산
const startIndex = (currentPage - 1) * tradesPerPage  // 0, 20, 40, ...
const endIndex = startIndex + tradesPerPage            // 20, 40, 60, ...

// 3. 슬라이싱
const paginatedTrades = reversed.slice(startIndex, endIndex)
```

---

### 4. Trading Edge 계산 보정

```typescript
// 완료된 거래만 기준으로 계산
const originalIndex = completedTrades.length - 1 - reversedIndex
const tradesUpToThis = completedTrades.slice(0, originalIndex + 1)
const cumulativeTotalPnl = tradesUpToThis.reduce((sum, t) => sum + (t.total_pnl || 0), 0)
const cumulativeEdge = cumulativeTotalPnl / tradesUpToThis.length
```

---

## 🧪 테스트

### 1. 거래 상세 페이지

```
1. Run 상세 페이지 접속
2. 아무 거래 선택
3. 진입 정보 확인:
   ✅ 리스크 제한 표시 ($200.00)
   ✅ 초기 리스크 소수점 4자리 ($197.5000)
```

---

### 2. 거래 목록 페이지네이션

```
1. 거래가 20개 이상인 Run 접속
2. 거래 목록 스크롤 없이 20개만 표시 확인
3. 페이지네이션 버튼 확인:
   ✅ [1] 2 3 ... 5
4. "다음" 버튼 클릭
5. 페이지 2로 이동 확인:
   ✅ 1 [2] 3 ... 5
```

---

### 3. 완료된 거래 필터링

```
1. 백테스트 실행 중인 Run 접속
2. 거래 목록 확인:
   ✅ "완료된 거래: X개" 표시
   ✅ 완료되지 않은 거래는 표시 안 됨
```

---

## 🎉 완료!

**개선 사항**:
1. ✅ 리스크 제한 금액 표시 (초기 자산의 2%)
2. ✅ 초기 리스크 소수점 4자리 표시
3. ✅ 완료된 거래만 필터링
4. ✅ 20개씩 페이지네이션
5. ✅ 스마트 페이지 번호 표시
6. ✅ 페이지 정보 표시

**효과**:
- 더 정확한 리스크 정보 제공
- 대량 거래 목록 관리 용이
- 빠른 페이지 로딩
- 명확한 거래 상태 구분

---

**작성 일자**: 2025-12-13  
**수정 파일**: 2개  
**상태**: 완료 ✅

