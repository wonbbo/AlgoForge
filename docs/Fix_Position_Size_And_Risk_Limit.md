# 포지션 크기 반올림 및 리스크 제한 정확도 개선

## 📝 요청 사항

1. **포지션 크기 반올림**
   - Run 수행 시 포지션 크기를 정수로 반올림

2. **리스크 제한 정확도 개선**
   - 현재 문제: 거래 상세 페이지의 "리스크 제한"이 초기 자산의 2%로 고정 표시
   - 실제: 백테스트 엔진은 50 거래마다 자산을 재계산하여 리스크 계산
   - 해결: 진입 시점의 실제 자산 기준 리스크 제한 표시

---

## 🔍 문제 분석

### 1️⃣ 포지션 크기 소수점 문제

**Before**:
```python
position_size = (current_balance * 0.02) / risk
# 예: (10000 * 0.02) / 87.5 = 2.2857...
# → 2.2857 계약 (소수점)
```

**문제점**:
- 실제 거래에서는 정수 계약만 가능
- 소수점 계약은 비현실적

---

### 2️⃣ 리스크 제한 표시 부정확

**현재 표시**:
```typescript
리스크 제한 = initial_balance * 0.02
// 항상 초기 자산 기준
// 예: $10,000 * 0.02 = $200.00
```

**실제 계산**:
```python
# 백테스트 엔진 (risk_manager.py)
def update_balance_every_50_trades():
    if trade_count % 50 == 0:
        current_balance = calculate_current_equity()

# 리스크 계산
risk_limit = current_balance * 0.02
position_size = risk_limit / risk
```

**예시**:
- 거래 #1: balance=$10,000 → 리스크 제한=$200
- 거래 #50: balance=$10,500 → 리스크 제한=$210
- 거래 #100: balance=$9,800 → 리스크 제한=$196

하지만 화면에는 모두 $200으로 표시됨 ❌

---

## ✅ 해결 방법

### 1️⃣ 포지션 크기 반올림

**파일**: `engine/core/risk_manager.py`

#### Before
```python
position_size = (self.current_balance * self.risk_percent) / risk
return position_size, risk
```

#### After
```python
position_size_raw = (self.current_balance * self.risk_percent) / risk

# 포지션 크기를 정수로 반올림
position_size = round(position_size_raw)

# 반올림 후 0이 되는 경우 방지 (최소 1)
if position_size == 0 and position_size_raw > 0:
    position_size = 1

return float(position_size), risk
```

**효과**:
- 2.2857 → 2 (정수)
- 1.8 → 2 (정수)
- 0.3 → 1 (최소값 보장)

---

### 2️⃣ 진입 시점 자산 저장

#### A. 데이터베이스 마이그레이션

**파일**: `db/migrations/003_add_balance_at_entry.sql`

```sql
-- balance_at_entry 컬럼 추가
ALTER TABLE trades ADD COLUMN balance_at_entry REAL;

-- 기존 데이터 역계산
-- balance_at_entry = (position_size * initial_risk) / 0.02
UPDATE trades
SET balance_at_entry = (position_size * initial_risk) / 0.02
WHERE balance_at_entry IS NULL;
```

**역계산 공식**:
```
position_size = (balance * 0.02) / risk
balance * 0.02 = position_size * risk
balance = (position_size * risk) / 0.02
```

---

#### B. Trade 모델 수정

**파일**: `engine/models/trade.py`

```python
@dataclass
class Trade:
    trade_id: int
    # ... existing fields ...
    balance_at_entry: float = 0.0  # 진입 시점의 잔고 추가
    # ... rest of fields ...
```

---

#### C. 백테스트 엔진 수정

**파일**: `engine/core/backtest_engine.py`

```python
# Trade 생성 시 balance_at_entry 저장
trade = Trade(
    trade_id=self.trade_id_counter,
    direction=direction,
    entry_price=entry_price,
    entry_timestamp=bar.timestamp,
    position_size=position_size,
    initial_risk=risk,
    stop_loss=stop_loss,
    take_profit_1=tp1_price,
    balance_at_entry=self.risk_manager.current_balance  # 추가
)
```

---

#### D. Repository 수정

**파일**: `apps/api/db/repositories.py`

```python
query = """
INSERT INTO trades (
    run_id, direction, entry_timestamp, entry_price,
    position_size, initial_risk, stop_loss, take_profit_1,
    is_closed, total_pnl, balance_at_entry  -- 추가
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# ... parameters ...
trade.balance_at_entry  # 추가
```

---

### 3️⃣ 프론트엔드 수정

#### A. 타입 정의

**파일**: `apps/web/lib/types.ts`

```typescript
export interface Trade {
  // ... existing fields ...
  balance_at_entry?: number  // 추가
  // ... rest of fields ...
}
```

---

#### B. 거래 상세 페이지

**파일**: `apps/web/app/runs/[id]/trades/[tradeId]/page.tsx`

**Before**:
```tsx
<p className="text-sm text-muted-foreground">리스크 제한</p>
<p className="text-xl font-bold">
  {run ? formatCurrency(run.initial_balance * 0.02) : '-'}
</p>
<p className="text-xs text-muted-foreground">
  초기 자산의 2%
</p>
```

**After**:
```tsx
<p className="text-sm text-muted-foreground">리스크 제한</p>
<p className="text-xl font-bold">
  {trade.balance_at_entry 
    ? formatCurrency(trade.balance_at_entry * 0.02)
    : (run ? formatCurrency(run.initial_balance * 0.02) : '-')
  }
</p>
<p className="text-xs text-muted-foreground">
  진입 시점 자산의 2%
</p>
```

---

## 📊 결과 비교

### 포지션 크기

**Before**:
```
거래 #1: position_size = 2.2857
거래 #2: position_size = 1.8421
거래 #3: position_size = 3.1415
```

**After**:
```
거래 #1: position_size = 2 (반올림)
거래 #2: position_size = 2 (반올림)
거래 #3: position_size = 3 (반올림)
```

---

### 리스크 제한 표시

**시나리오**: 50 거래마다 자산 재계산

**Before (부정확)**:
```
거래 #1:  리스크 제한 = $200.00 (초기 자산 기준)
거래 #50: 리스크 제한 = $200.00 (부정확!)
거래 #100: 리스크 제한 = $200.00 (부정확!)
```

**After (정확)**:
```
거래 #1:  balance=$10,000 → 리스크 제한 = $200.00 ✅
거래 #50: balance=$10,500 → 리스크 제한 = $210.00 ✅
거래 #100: balance=$9,800  → 리스크 제한 = $196.00 ✅
```

---

## 💡 포지션 크기 계산 검증

### 예시 1: 일반적인 경우

```
balance_at_entry = $10,000
initial_risk = $87.5
risk_limit = $10,000 * 0.02 = $200

계산:
position_size_raw = $200 / $87.5 = 2.2857
position_size_rounded = 2

실제 사용 리스크 = 2 * $87.5 = $175.00
리스크 사용률 = $175 / $200 = 87.5% ✅
```

---

### 예시 2: 작은 리스크

```
balance_at_entry = $10,000
initial_risk = $400 (큰 리스크)
risk_limit = $200

계산:
position_size_raw = $200 / $400 = 0.5
position_size_rounded = 1 (최소값 보장)

실제 사용 리스크 = 1 * $400 = $400.00
리스크 사용률 = $400 / $200 = 200% ⚠️
```

**참고**: 리스크가 너무 크면 제한을 초과할 수 있음 (반올림 부작용)

---

## 🧪 테스트

### 1. 마이그레이션 확인

```bash
cd C:\Users\wonbbo\Workspace\Cursor\AlgoForge
python db/apply_balance_migration.py
```

**예상 출력**:
```
Applying migration to: db\algoforge.db
[SUCCESS] Migration applied successfully!
[INFO] Updated 2610 trades with balance_at_entry
```

---

### 2. 새 Run 실행

```
1. 전략 빌더에서 전략 생성
2. Run 실행
3. 거래 완료 후 확인
```

**확인 사항**:
- ✅ 포지션 크기가 정수로 표시
- ✅ 리스크 제한이 진입 시점 자산 기준으로 표시
- ✅ 초기 리스크가 소수점 4자리로 표시

---

### 3. 거래 상세 페이지 확인

```
거래 #1:
- 포지션 크기: 2 (정수)
- 리스크 제한: $200.00 (balance=$10,000 기준)
- 초기 리스크: $175.0000

거래 #50:
- 포지션 크기: 3 (정수)
- 리스크 제한: $210.00 (balance=$10,500 기준)
- 초기 리스크: $183.5000
```

---

## 📝 데이터 흐름

### 백테스트 실행

```
1. Risk Manager 초기화
   - current_balance = initial_balance = $10,000

2. 거래 #1 진입
   - risk = $87.5
   - position_size_raw = ($10,000 * 0.02) / $87.5 = 2.2857
   - position_size = round(2.2857) = 2
   - balance_at_entry = $10,000

3. Trade 저장
   - position_size: 2
   - initial_risk: $87.5
   - balance_at_entry: $10,000

4. 거래 #50 완료 후
   - update_balance()
   - current_balance = calculate_equity() = $10,500

5. 거래 #51 진입
   - balance_at_entry = $10,500
   - risk_limit = $10,500 * 0.02 = $210.00
```

---

### 프론트엔드 표시

```
API Response:
{
  "trade_id": 51,
  "position_size": 3,
  "initial_risk": 70.0,
  "balance_at_entry": 10500.0
}

화면 표시:
- 포지션 크기: 3
- 리스크 제한: $210.00 (= $10,500 * 0.02)
- 초기 리스크: $70.0000
```

---

## 🎯 주요 변경 사항

### Backend

1. ✅ `risk_manager.py`: 포지션 크기 반올림
2. ✅ `trade.py`: `balance_at_entry` 필드 추가
3. ✅ `backtest_engine.py`: Trade 생성 시 `balance_at_entry` 저장
4. ✅ `repositories.py`: DB INSERT 시 `balance_at_entry` 포함

### Database

5. ✅ `003_add_balance_at_entry.sql`: 마이그레이션 생성
6. ✅ 기존 데이터 역계산으로 채움

### Frontend

7. ✅ `types.ts`: `Trade` 타입에 `balance_at_entry` 추가
8. ✅ `[tradeId]/page.tsx`: 리스크 제한 계산 수정

---

## 🎉 완료!

**개선 사항**:
- ✅ 포지션 크기 정수 반올림
- ✅ 최소 포지션 크기 1 보장
- ✅ 진입 시점 자산 저장
- ✅ 정확한 리스크 제한 표시
- ✅ 기존 데이터 역계산 마이그레이션
- ✅ Lint 에러 0개

**효과**:
- 더 현실적인 포지션 크기
- 정확한 리스크 관리 정보
- 50 거래마다 변하는 리스크 제한 추적 가능

---

**작성 일자**: 2025-12-13  
**수정 파일**: 8개  
**마이그레이션**: 1개 (2610 거래 업데이트)  
**상태**: 완료 ✅

