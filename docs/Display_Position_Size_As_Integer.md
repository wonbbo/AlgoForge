# 포지션 크기 정수 표시

## 📝 요청 사항

포지션 크기를 소수점 없이 정수로 표시

---

## 현재 상태

### Backend
- ✅ 이미 정수로 계산 (`risk_manager.py`)
  ```python
  position_size = round(position_size_raw)  # 반올림
  ```

### Frontend
- ❌ 소수점 4자리로 표시
  ```tsx
  {trade.position_size.toFixed(4)}
  // 예: 2.0000
  ```

---

## ✅ 해결 방법

### 거래 상세 페이지 수정

**파일**: `apps/web/app/runs/[id]/trades/[tradeId]/page.tsx`

#### Before
```tsx
<div>
  <p className="text-sm text-muted-foreground">포지션 크기</p>
  <p className="font-medium">{trade.position_size.toFixed(4)}</p>
</div>
```

**표시**: `2.0000`

---

#### After
```tsx
<div>
  <p className="text-sm text-muted-foreground">포지션 크기</p>
  <p className="font-medium">{Math.round(trade.position_size)}</p>
</div>
```

**표시**: `2`

---

## 📊 변경 비교

### Before (소수점 4자리)
```
진입 정보
├─ 진입 시각: 2024-01-01 12:00:00
├─ 진입가: $50,000.00
└─ 포지션 크기: 2.0000  ← 소수점
```

### After (정수)
```
진입 정보
├─ 진입 시각: 2024-01-01 12:00:00
├─ 진입가: $50,000.00
└─ 포지션 크기: 2  ← 깔끔!
```

---

## 💡 Math.round() 사용 이유

### 옵션 1: `Math.floor()` (내림)
```typescript
Math.floor(2.9) → 2
Math.floor(2.1) → 2
```

### 옵션 2: `Math.ceil()` (올림)
```typescript
Math.ceil(2.1) → 3
Math.ceil(2.9) → 3
```

### 옵션 3: `Math.round()` (반올림) ✅
```typescript
Math.round(2.1) → 2
Math.round(2.9) → 3
```

**선택 이유**: 백엔드에서 이미 `round()`로 계산하므로 일관성 유지

---

## 🧪 테스트

### 1. 브라우저 새로고침
```
Ctrl + Shift + R
http://localhost:3000/runs/{run_id}
```

### 2. 거래 상세 확인
```
1. 아무 거래 클릭
2. 진입 정보 확인:
   ✅ 포지션 크기: 2 (소수점 없음)
```

### 3. 다양한 값 확인
```
거래 #1: 2.0000 → 2
거래 #2: 1.0000 → 1
거래 #3: 3.0000 → 3
```

---

## 🎯 일관성

### Backend 계산
```python
# engine/core/risk_manager.py
position_size_raw = (balance * 0.02) / risk
position_size = round(position_size_raw)  # 정수 반올림
return float(position_size), risk  # float 타입으로 반환 (2.0)
```

### DB 저장
```sql
-- trades 테이블
position_size REAL  -- 2.0 (float 타입)
```

### Frontend 표시
```tsx
// Before
{trade.position_size.toFixed(4)}  // "2.0000"

// After
{Math.round(trade.position_size)}  // 2 (number 타입, 정수로 표시)
```

---

## 📝 다른 화면 확인

### 거래 목록 (runs/[id]/page.tsx)
- 포지션 크기 표시 없음 ✅

### 차트 (TradeChart 컴포넌트)
- 포지션 크기 표시 없음 ✅

### Run 상세 (Metrics)
- 포지션 크기 표시 없음 ✅

**결론**: 거래 상세 페이지에만 표시됨

---

## 🎉 완료!

**변경 사항**:
- ✅ 포지션 크기 정수 표시
- ✅ 소수점 제거
- ✅ Lint 에러 0개

**수정 파일**: 1개
- `apps/web/app/runs/[id]/trades/[tradeId]/page.tsx`

**효과**:
- 더 깔끔한 UI
- 백엔드와 일관성
- 실제 거래 계약 수와 일치

---

**작성 일자**: 2025-12-13  
**수정 파일**: 1개  
**상태**: 완료 ✅

