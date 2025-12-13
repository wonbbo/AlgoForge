# API 응답에 balance_at_entry 필드 추가

## 📝 문제

거래 상세 페이지에서 리스크 제한이 여전히 초기 자산($10,000) 기준인 $200로 표시되는 문제.

**원인**: API 스키마에 `balance_at_entry` 필드가 누락되어 응답에 포함되지 않음.

---

## 🔍 진단

### 1. DB 확인
```sql
SELECT trade_id, balance_at_entry FROM trades LIMIT 5;

-- 결과:
-- trade_id | balance_at_entry
-- 5737     | 10000.00  ✅ (저장되어 있음)
-- 5738     | 10000.00  ✅
```

### 2. API 스키마 확인
```python
# apps/api/schemas/trade.py (Before)
class TradeResponse(BaseModel):
    trade_id: int
    # ...
    take_profit_1: float
    # balance_at_entry 없음! ❌
    is_closed: bool
```

### 3. 프론트엔드 타입 확인
```typescript
// apps/web/lib/types.ts
export interface Trade {
  // ...
  balance_at_entry?: number  // ✅ (이미 추가됨)
  // ...
}
```

---

## ✅ 해결 방법

### API 스키마에 필드 추가

**파일**: `apps/api/schemas/trade.py`

```python
class TradeResponse(BaseModel):
    """Trade 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    trade_id: int
    run_id: int
    direction: str
    entry_timestamp: int
    entry_price: float
    position_size: float
    initial_risk: float
    stop_loss: float
    take_profit_1: float
    balance_at_entry: Optional[float] = None  # ← 추가
    is_closed: bool
    total_pnl: Optional[float]
    legs: list[TradeLegResponse] = []
```

---

## 📊 데이터 흐름

### Before (누락)

```
DB Query:
SELECT * FROM trades WHERE run_id = ?
→ balance_at_entry: 10500.0 (포함됨)

API Schema (TradeResponse):
❌ balance_at_entry 필드 없음

API Response:
{
  "trade_id": 51,
  "position_size": 3,
  "initial_risk": 70.0,
  // balance_at_entry 없음 ❌
}

Frontend:
trade.balance_at_entry → undefined
→ fallback: run.initial_balance * 0.02 = $200 ❌
```

---

### After (포함)

```
DB Query:
SELECT * FROM trades WHERE run_id = ?
→ balance_at_entry: 10500.0 (포함됨)

API Schema (TradeResponse):
✅ balance_at_entry: Optional[float] = None

API Response:
{
  "trade_id": 51,
  "position_size": 3,
  "initial_risk": 70.0,
  "balance_at_entry": 10500.0  // ✅ 포함됨
}

Frontend:
trade.balance_at_entry → 10500.0
→ 리스크 제한 = 10500.0 * 0.02 = $210.00 ✅
```

---

## 🧪 테스트

### 1. API 서버 재시작 (필수!)

```bash
stop_server.bat
start_server.bat
```

**중요**: 스키마 변경이므로 서버 재시작 필수!

---

### 2. API 응답 확인

#### 방법 1: 브라우저 Network 탭

```
1. F12 → Network 탭
2. 거래 상세 페이지 접속
3. API 요청 확인:
   GET /api/runs/{run_id}/trades

4. Response 확인:
{
  "trades": [
    {
      "trade_id": 51,
      "balance_at_entry": 10500.0  // ✅ 있어야 함
    }
  ]
}
```

---

#### 방법 2: curl 테스트

```bash
curl http://localhost:8000/api/runs/1/trades
```

**기대 응답**:
```json
{
  "trades": [
    {
      "trade_id": 1,
      "balance_at_entry": 10000.0
    }
  ],
  "total": 87
}
```

---

### 3. 프론트엔드 표시 확인

```
거래 상세 페이지:

진입 정보
├─ 매수 규모: $25,000.00
├─ 리스크 제한: $210.00  ← 변경됨! (이전: $200)
└─ 초기 리스크: $70.0000
```

---

## 📝 검증 시나리오

### 시나리오 1: 거래 #1 (초기)

```
DB:
- balance_at_entry = 10000.0

API Response:
- balance_at_entry: 10000.0

Frontend 계산:
- 리스크 제한 = 10000.0 * 0.02 = $200.00 ✅
```

---

### 시나리오 2: 거래 #51 (50거래 후 재평가)

```
DB:
- balance_at_entry = 10500.0

API Response:
- balance_at_entry: 10500.0

Frontend 계산:
- 리스크 제한 = 10500.0 * 0.02 = $210.00 ✅
```

---

### 시나리오 3: 거래 #101 (손실 후)

```
DB:
- balance_at_entry = 9800.0

API Response:
- balance_at_entry: 9800.0

Frontend 계산:
- 리스크 제한 = 9800.0 * 0.02 = $196.00 ✅
```

---

## 🔧 Repository 동작 확인

**Repository는 수정 불필요**:

```python
# apps/api/db/repositories.py
def get_by_run(self, run_id: int) -> List[Dict[str, Any]]:
    query = "SELECT * FROM trades WHERE run_id = ?"
    # ↑ SELECT * 이므로 balance_at_entry 자동 포함 ✅
```

**Router 동작**:

```python
# apps/api/routers/runs.py
trades = trade_repo.get_by_run(run_id)

for trade in trades:
    trade_response = TradeResponse(**trade, legs=...)
    # ↑ **trade는 balance_at_entry 포함 ✅
    # TradeResponse 스키마에 필드 있으면 자동 매핑 ✅
```

---

## 🎯 핵심 변경

**수정 파일**: 1개
- `apps/api/schemas/trade.py`: `balance_at_entry` 필드 추가

**영향 범위**:
- GET `/api/runs/{run_id}/trades` - Trade 목록 조회
- 거래 상세 페이지의 리스크 제한 표시

---

## 💡 왜 누락되었나?

### 개발 순서

1. ✅ DB 마이그레이션 (balance_at_entry 컬럼 추가)
2. ✅ 백엔드 모델 수정 (Trade 클래스)
3. ✅ Repository 수정 (INSERT 문)
4. ✅ 프론트엔드 타입 수정 (Trade interface)
5. ✅ 프론트엔드 표시 로직 수정
6. ❌ **API 스키마 수정 누락** ← 여기서 놓침!

### 교훈

**모든 레이어 확인 필요**:
```
DB Schema
  ↓
Backend Model
  ↓
Repository (CRUD)
  ↓
API Schema (Response/Request)  ← 여기도 확인!
  ↓
Frontend Type
  ↓
Frontend UI
```

---

## 🎉 완료!

**수정 사항**:
- ✅ API 스키마에 `balance_at_entry` 필드 추가
- ✅ Optional 타입으로 설정 (기존 데이터 호환)
- ✅ Lint 에러 0개

**다음 단계**:
1. **API 서버 재시작** (필수!)
2. 브라우저 새로고침
3. 거래 상세 페이지에서 리스크 제한 확인

---

**작성 일자**: 2025-12-13  
**수정 파일**: 1개 (schemas/trade.py)  
**상태**: 완료 ✅

