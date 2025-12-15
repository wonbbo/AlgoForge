# OHLCV 조건 기능 구현 완료

## 개요
AlgoForge 전략 조건에 **OHLCV (Open, High, Low, Close, Volume)** 값을 직접 사용할 수 있는 기능을 구현했습니다.

## 구현 내용

### 1. Backend 엔진 수정
**파일**: `engine/utils/strategy_parser.py`

- `_get_value()` 메서드에 `volume` 처리 추가
- 기존에 `open`, `high`, `low`, `close`는 지원되고 있었고, `volume` 추가로 완성

```python
# price 필드 참조 (예: {"price": "close"})
elif "price" in value_def:
    price_field = value_def["price"]
    bar = self.bars[bar_index]
    
    if price_field == "open":
        return bar.open
    elif price_field == "high":
        return bar.high
    elif price_field == "low":
        return bar.low
    elif price_field == "close":
        return bar.close
    elif price_field == "volume":  # 새로 추가
        return bar.volume
```

### 2. 문서 작성

#### 2.1 OHLCV 사용 가이드
**파일**: `docs/Strategy_OHLCV_Usage_Guide.md`

- OHLCV 값 사용 방법 상세 설명
- 5가지 실전 예시 제공
- UI 구현 가이드 포함

#### 2.2 예제 전략 JSON
**파일**: `docs/examples/strategy_with_ohlcv_conditions.json`

- Close > EMA 조건
- Volume > 평균 Volume 조건
- 롱/숏 양방향 진입 조건 예시

#### 2.3 Strategy Builder Implementation Guide 업데이트
**파일**: `docs/AlgoForge_Strategy_Builder_Implementation_Guide_v1.0.md`

- ConditionDraft 타입에 `price` 타입 추가
- ConditionRow 컴포넌트 UI 확장 가이드
- Draft → JSON 변환 로직 업데이트

### 3. 테스트 작성
**파일**: `tests/test_strategy_parser_ohlcv.py`

5가지 테스트 케이스 작성 및 모두 통과:
1. ✅ Close > EMA 조건
2. ✅ Volume > 평균 Volume 조건
3. ✅ 복합 조건 (Close > EMA AND Volume > 평균)
4. ✅ Close cross_above EMA 조건
5. ✅ 모든 OHLCV 필드 테스트

## 사용 예시

### 예시 1: Close가 EMA 위에 있을 때 진입
```json
{
  "entry": {
    "long": {
      "and": [
        {
          "left": { "price": "close" },
          "op": ">",
          "right": { "ref": "ema_20" }
        }
      ]
    }
  }
}
```

### 예시 2: 거래량 증가 + 가격 돌파 조건
```json
{
  "entry": {
    "long": {
      "and": [
        {
          "left": { "price": "close" },
          "op": "cross_above",
          "right": { "ref": "ema_20" }
        },
        {
          "left": { "price": "volume" },
          "op": ">",
          "right": { "ref": "sma_volume" }
        }
      ]
    }
  }
}
```

## 지원하는 OHLCV 필드

| 필드 | 설명 | JSON 표기 |
|------|------|-----------|
| Open | 시가 | `{"price": "open"}` |
| High | 고가 | `{"price": "high"}` |
| Low | 저가 | `{"price": "low"}` |
| Close | 종가 | `{"price": "close"}` |
| Volume | 거래량 | `{"price": "volume"}` |

## 지원하는 연산자

| 연산자 | 설명 | 예시 |
|--------|------|------|
| `>` | 크다 | close > ema_20 |
| `<` | 작다 | close < ema_20 |
| `>=` | 크거나 같다 | high >= 50000 |
| `<=` | 작거나 같다 | low <= 45000 |
| `==` | 같다 | rsi == 50 |
| `cross_above` | 상향 돌파 | close cross_above ema_20 |
| `cross_below` | 하향 돌파 | close cross_below ema_20 |

## 조건 구조

### 좌변/우변에 올 수 있는 값
1. **지표 참조**: `{"ref": "indicator_id"}`
2. **OHLCV 값**: `{"price": "open|high|low|close|volume"}`
3. **상수 값**: `{"value": 100}`

### 예시 조합
- ✅ OHLCV vs 지표: `{"price": "close"}` > `{"ref": "ema_20"}`
- ✅ OHLCV vs 상수: `{"price": "high"}` >= `{"value": 50000}`
- ✅ 지표 vs 지표: `{"ref": "ema_fast"}` cross_above `{"ref": "ema_slow"}`
- ✅ 지표 vs 상수: `{"ref": "rsi"}` > `{"value": 70}`

## Frontend UI 구현 시 참고사항

### ConditionRow 컴포넌트 확장
조건 선택 드롭다운에 OHLCV 옵션 추가:

```typescript
<SelectContent>
  {/* OHLCV 옵션 */}
  <div className="px-2 py-1.5 text-xs font-semibold">
    OHLCV
  </div>
  <SelectItem value="open">Open (시가)</SelectItem>
  <SelectItem value="high">High (고가)</SelectItem>
  <SelectItem value="low">Low (저가)</SelectItem>
  <SelectItem value="close">Close (종가)</SelectItem>
  <SelectItem value="volume">Volume (거래량)</SelectItem>
  
  {/* 구분선 */}
  <div className="h-px bg-border my-1" />
  
  {/* 지표 옵션 */}
  <div className="px-2 py-1.5 text-xs font-semibold">
    지표
  </div>
  {indicators.map(ind => (
    <SelectItem key={ind.id} value={ind.id}>
      {ind.id} ({ind.type})
    </SelectItem>
  ))}
</SelectContent>
```

### Draft State 타입 확장
```typescript
export interface ConditionDraft {
  tempId: string;
  
  left: {
    type: 'indicator' | 'price' | 'number';
    value: string | number;
  };
  
  operator: '>' | '<' | '>=' | '<=' | '==' | 'cross_above' | 'cross_below';
  
  right: {
    type: 'indicator' | 'price' | 'number';
    value: string | number;
  };
}
```

## 테스트 결과

```
[Test 1] Close > EMA condition                    ✅ PASS
[Test 2] Volume > average Volume condition        ✅ PASS
[Test 3] Combined condition                       ✅ PASS
[Test 4] Close cross_above EMA condition          ✅ PASS
[Test 5] All OHLCV fields test                    ✅ PASS

ALL OHLCV TESTS PASSED!
```

## 다음 단계

1. **Frontend UI 구현**
   - Strategy Builder에 OHLCV 선택 옵션 추가
   - ConditionRow 컴포넌트 확장

2. **추가 예제 작성**
   - 다양한 OHLCV 조합 전략 예시
   - 실전 전략 템플릿

3. **사용자 문서 업데이트**
   - 초보자 가이드
   - 전략 작성 튜토리얼

## 관련 파일

- ✅ `engine/utils/strategy_parser.py` - OHLCV 처리 로직
- ✅ `docs/Strategy_OHLCV_Usage_Guide.md` - 사용 가이드
- ✅ `docs/examples/strategy_with_ohlcv_conditions.json` - 예제 전략
- ✅ `docs/AlgoForge_Strategy_Builder_Implementation_Guide_v1.0.md` - UI 가이드
- ✅ `tests/test_strategy_parser_ohlcv.py` - 테스트 코드

## 결론

OHLCV 조건 기능이 성공적으로 구현되었습니다. 이제 사용자는 다음과 같은 고급 전략을 작성할 수 있습니다:

- 💡 가격이 특정 지표 위/아래에 있을 때 진입
- 💡 거래량이 평균보다 많을 때만 진입
- 💡 고가/저가 돌파 전략
- 💡 복합 조건 (가격 + 거래량 + 지표)

**모든 테스트 통과 및 문서 작성 완료!** 🎉

