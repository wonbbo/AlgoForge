# OHLCV 값을 조건에서 사용하기

## 개요
AlgoForge에서는 전략 조건에서 **OHLCV (Open, High, Low, Close, Volume)** 값을 직접 사용할 수 있습니다.

예를 들어:
- "Close가 EMA 위에 있을 때"
- "High가 특정 값을 돌파할 때"
- "Volume이 평균 Volume보다 클 때"

## 사용 방법

### JSON 구조
OHLCV 값을 조건에서 사용하려면 `price` 필드를 사용합니다:

```json
{
  "left": { "price": "close" },
  "op": ">",
  "right": { "ref": "ema_20" }
}
```

### 지원하는 OHLCV 필드
| 필드 | 설명 | 예시 |
|------|------|------|
| `open` | 시가 | `{"price": "open"}` |
| `high` | 고가 | `{"price": "high"}` |
| `low` | 저가 | `{"price": "low"}` |
| `close` | 종가 | `{"price": "close"}` |
| `volume` | 거래량 | `{"price": "volume"}` |

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

**설명**: 현재 봉의 종가(close)가 EMA(20) 위에 있으면 롱 진입

### 예시 2: Close가 EMA를 상향 돌파할 때
```json
{
  "entry": {
    "long": {
      "and": [
        {
          "left": { "price": "close" },
          "op": "cross_above",
          "right": { "ref": "ema_20" }
        }
      ]
    }
  }
}
```

**설명**: 종가가 EMA(20)을 상향 돌파할 때 롱 진입

### 예시 3: Volume이 평균보다 클 때
```json
{
  "indicators": [
    {
      "id": "sma_volume",
      "type": "sma",
      "params": {
        "source": "volume",
        "period": 20
      }
    }
  ],
  "entry": {
    "long": {
      "and": [
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

**설명**: 현재 거래량이 20봉 평균 거래량보다 클 때 진입

### 예시 4: High가 특정 값 이상일 때
```json
{
  "entry": {
    "long": {
      "and": [
        {
          "left": { "price": "high" },
          "op": ">=",
          "right": { "value": 50000 }
        }
      ]
    }
  }
}
```

**설명**: 현재 봉의 고가가 50000 이상일 때 진입

### 예시 5: 복합 조건 - Close와 Volume 동시 체크
```json
{
  "indicators": [
    {
      "id": "ema_20",
      "type": "ema",
      "params": {
        "source": "close",
        "period": 20
      }
    },
    {
      "id": "sma_volume",
      "type": "sma",
      "params": {
        "source": "volume",
        "period": 20
      }
    }
  ],
  "entry": {
    "long": {
      "and": [
        {
          "left": { "price": "close" },
          "op": ">",
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

**설명**: 
- 종가가 EMA(20) 위에 있고 (AND)
- 거래량이 20봉 평균 거래량보다 클 때 진입

## 조건 구조 요약

### 좌변/우변에 올 수 있는 값 타입
1. **지표 참조**: `{"ref": "indicator_id"}`
2. **OHLCV 값**: `{"price": "open|high|low|close|volume"}`
3. **상수 값**: `{"value": 100}`

### 사용 가능한 연산자
| 연산자 | 설명 | 예시 |
|--------|------|------|
| `>` | 크다 | close > ema_20 |
| `<` | 작다 | close < ema_20 |
| `>=` | 크거나 같다 | high >= 50000 |
| `<=` | 작거나 같다 | low <= 45000 |
| `==` | 같다 | rsi == 50 |
| `cross_above` | 상향 돌파 | close cross_above ema_20 |
| `cross_below` | 하향 돌파 | close cross_below ema_20 |

**주의**: `cross_above`, `cross_below`는 양쪽 모두 **지표 또는 OHLCV**여야 합니다. 상수 값과는 사용 불가.

## 실전 전략 예시

### 전략: "볼륨 확인 EMA 크로스"
```json
{
  "schema_version": "1.0",
  "meta": {
    "name": "볼륨 확인 EMA 크로스",
    "description": "EMA 크로스 + 거래량 증가 확인"
  },
  "indicators": [
    {
      "id": "ema_fast",
      "type": "ema",
      "params": {
        "source": "close",
        "period": 12
      }
    },
    {
      "id": "ema_slow",
      "type": "ema",
      "params": {
        "source": "close",
        "period": 26
      }
    },
    {
      "id": "sma_volume",
      "type": "sma",
      "params": {
        "source": "volume",
        "period": 20
      }
    }
  ],
  "entry": {
    "long": {
      "and": [
        {
          "left": { "ref": "ema_fast" },
          "op": "cross_above",
          "right": { "ref": "ema_slow" }
        },
        {
          "left": { "price": "volume" },
          "op": ">",
          "right": { "ref": "sma_volume" }
        }
      ]
    },
    "short": {
      "and": [
        {
          "left": { "ref": "ema_fast" },
          "op": "cross_below",
          "right": { "ref": "ema_slow" }
        },
        {
          "left": { "price": "volume" },
          "op": ">",
          "right": { "ref": "sma_volume" }
        }
      ]
    }
  },
  "stop_loss": {
    "type": "fixed_percent",
    "percent": 2.0
  },
  "reverse": {
    "enabled": true,
    "mode": "use_entry_opposite"
  },
  "hook": {
    "enabled": false
  }
}
```

**전략 설명**:
- **롱 진입**: EMA 빠른선이 느린선을 상향 돌파하고, 거래량이 평균보다 클 때
- **숏 진입**: EMA 빠른선이 느린선을 하향 돌파하고, 거래량이 평균보다 클 때
- **청산**: 반대 방향 진입 신호 발생 시 (Reverse)

## UI에서 사용하기 (Strategy Builder)

### ConditionRow 컴포넌트 확장 필요
현재 Strategy Builder UI를 구현할 때는 다음과 같이 OHLCV 선택 옵션을 추가해야 합니다:

```typescript
// ConditionRow.tsx에서 좌변/우변 선택 시
<Select
  value={condition.left.value.toString()}
  onValueChange={(value) => {
    // indicator, price, number 판별
    if (value === '__number__') {
      onChange({
        ...condition,
        left: { type: 'number', value: 0 }
      });
    } else if (['open', 'high', 'low', 'close', 'volume'].includes(value)) {
      onChange({
        ...condition,
        left: { type: 'price', value: value }
      });
    } else {
      onChange({
        ...condition,
        left: { type: 'indicator', value: value }
      });
    }
  }}
>
  <SelectTrigger className="w-[200px]">
    <SelectValue placeholder="좌변 선택" />
  </SelectTrigger>
  <SelectContent>
    {/* OHLCV 옵션 */}
    <SelectItem value="open">Open (시가)</SelectItem>
    <SelectItem value="high">High (고가)</SelectItem>
    <SelectItem value="low">Low (저가)</SelectItem>
    <SelectItem value="close">Close (종가)</SelectItem>
    <SelectItem value="volume">Volume (거래량)</SelectItem>
    
    {/* 구분선 */}
    <div className="h-px bg-border my-1" />
    
    {/* 지표 옵션 */}
    {indicators.map(ind => (
      <SelectItem key={ind.id} value={ind.id}>
        {ind.id} ({ind.type})
      </SelectItem>
    ))}
    
    {/* 구분선 */}
    <div className="h-px bg-border my-1" />
    
    {/* 숫자 입력 */}
    <SelectItem value="__number__">숫자 입력</SelectItem>
  </SelectContent>
</Select>
```

### Draft State 타입 확장
```typescript
// types/strategy-draft.ts
export interface ConditionDraft {
  tempId: string;
  
  left: {
    type: 'indicator' | 'price' | 'number';
    value: string | number;  // price면 'open'|'high'|'low'|'close'|'volume'
  };
  
  operator: '>' | '<' | '>=' | '<=' | '==' | 'cross_above' | 'cross_below';
  
  right: {
    type: 'indicator' | 'price' | 'number';
    value: string | number;
  };
}
```

### Draft → JSON 변환
```typescript
// lib/draft-to-json.ts
function convertCondition(condition: ConditionDraft): ConditionJSON {
  return {
    left: convertValue(condition.left),
    op: condition.operator,
    right: convertValue(condition.right)
  };
}

function convertValue(value: { type: string; value: string | number }) {
  if (value.type === 'indicator') {
    return { ref: value.value as string };
  } else if (value.type === 'price') {
    return { price: value.value as string };
  } else {
    return { value: value.value as number };
  }
}
```

## 제약 사항

### ❌ 지원하지 않는 조건
1. **OHLCV 간의 Cross 연산**
   ```json
   // 잘못된 예
   {
     "left": { "price": "high" },
     "op": "cross_above",
     "right": { "price": "close" }
   }
   ```
   **이유**: Cross는 시계열 비교이므로 지표 간에만 의미가 있습니다.

2. **Volume을 이용한 Cross**
   ```json
   // 사용 가능하지만 의미가 없을 수 있음
   {
     "left": { "price": "volume" },
     "op": "cross_above",
     "right": { "ref": "sma_volume" }
   }
   ```
   **권장**: Volume은 `>`, `<` 연산자 사용

### ✅ 권장 사용법
1. **가격(OHLCV) vs 지표**: 대부분의 경우 적합
2. **가격(OHLCV) vs 상수**: 지지/저항선 체크 시 유용
3. **지표 vs 지표**: 크로스 전략에 적합

## 결론

OHLCV 값을 조건에 추가함으로써 다음과 같은 전략을 구현할 수 있습니다:
- ✅ 가격이 특정 지표 위/아래에 있을 때
- ✅ 거래량이 평균보다 많을 때
- ✅ 고가/저가가 특정 값을 돌파할 때
- ✅ 복합 조건 (가격 + 거래량 + 지표)

**Next Steps**:
1. 예제 전략 JSON 작성
2. 백테스트 실행 및 검증
3. UI에서 OHLCV 선택 옵션 구현 (Frontend 개발 시)

