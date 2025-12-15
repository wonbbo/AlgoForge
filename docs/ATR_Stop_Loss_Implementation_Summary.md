# ATR 기반 손절 (stop_loss type 'atr_based') 구현 완료

## 개요
ATR (Average True Range) 기반 동적 손절가 계산 기능을 구현했습니다. 시장 변동성에 따라 자동으로 손절선이 조정되어 더 효과적인 리스크 관리가 가능합니다.

## ATR이란?

### Average True Range (평균 진폭)
- **목적**: 시장의 변동성을 측정하는 지표
- **특징**: 가격 변동폭이 클수록 ATR 값이 높음
- **사용**: 손절가, 포지션 사이즈 결정에 주로 활용

### True Range 계산
```
TR = max(
  high - low,
  abs(high - prev_close),
  abs(low - prev_close)
)
```

### ATR 계산
```
ATR = SMA(TR, period)
```

일반적으로 period=14를 사용합니다.

## 구현 내용

### 1. ATR 지표 계산 ✅
**파일**: `engine/utils/indicators.py`

#### 추가된 메서드
```python
def calculate_atr(self, indicator_id: str, period: int) -> None:
    """
    ATR (Average True Range) 계산
    
    Args:
        indicator_id: 지표 ID (예: "atr_1")
        period: 기간 (기본 14)
    """
```

#### 계산 로직
1. **True Range 계산**
   - 첫 번째 봉: `TR = high - low`
   - 이후 봉: `TR = max(high - low, |high - prev_close|, |low - prev_close|)`

2. **ATR 계산**
   - True Range의 이동평균 (SMA)
   - `ATR = SMA(TR, period)`

### 2. Strategy Parser ATR 지표 타입 추가 ✅
**파일**: `engine/utils/strategy_parser.py`

#### _calculate_indicators() 메서드 확장
```python
elif indicator_type == "atr":
    period = params.get("period", 14)
    self.indicator_calc.calculate_atr(indicator_id, period)
```

### 3. ATR 기반 손절가 계산 구현 ✅
**파일**: `engine/utils/strategy_parser.py`

#### _calculate_stop_loss() 메서드 확장
```python
elif sl_type == "atr_based":
    # ATR 기반 손절가 계산
    atr_indicator_id = stop_loss_def.get("atr_indicator_id")
    multiplier = stop_loss_def.get("multiplier", 2.0)
    
    # ATR 값 가져오기
    atr_value = self.indicator_calc.get_value(atr_indicator_id, bar_index)
    
    # 손절가 계산
    if direction == "LONG":
        stop_loss = entry_price - (atr_value * multiplier)
    else:  # SHORT
        stop_loss = entry_price + (atr_value * multiplier)
```

#### 계산 공식
- **LONG**: `SL = Entry - (ATR × Multiplier)`
- **SHORT**: `SL = Entry + (ATR × Multiplier)`

### 4. 테스트 작성 및 통과 ✅
**파일**: `tests/test_atr_stop_loss.py`

5가지 테스트 케이스:
1. ✅ ATR 계산
2. ✅ ATR 기반 손절가 (LONG)
3. ✅ ATR 기반 손절가 (SHORT)
4. ✅ 다양한 ATR multiplier
5. ✅ True Range 계산 검증

#### 테스트 결과
```
============================================================
ALL ATR TESTS PASSED!
============================================================

[Test 1] ATR 계산                                ✅ PASS
[Test 2] ATR 기반 손절가 (LONG)                  ✅ PASS
[Test 3] ATR 기반 손절가 (SHORT)                 ✅ PASS
[Test 4] 다양한 ATR multiplier                    ✅ PASS
[Test 5] True Range 계산 검증                     ✅ PASS
```

## 사용 방법

### 1. 전략 JSON에서 사용

```json
{
  "indicators": [
    {
      "id": "atr_14",
      "type": "atr",
      "params": {
        "period": 14
      }
    }
  ],
  "stop_loss": {
    "type": "atr_based",
    "atr_indicator_id": "atr_14",
    "multiplier": 2.0
  }
}
```

### 2. 프론트엔드 UI에서 사용

#### Step 1: ATR 지표 추가
1. "Step 1: 지표 선택" 화면
2. "ATR (평균 진폭)" 카드에서 "추가" 버튼 클릭
3. Period 설정 (기본값: 14)

#### Step 3: ATR 기반 손절 선택
1. "Step 3: 손절 방식 선택" 화면
2. "ATR 기반 (ATR Based)" 선택
3. ATR 지표 선택 (Step 1에서 추가한 ATR 지표)
4. ATR 배수 설정 (Multiplier, 기본값: 2.0)

## 파라미터 설명

### period (ATR 계산 기간)
- **기본값**: 14
- **범위**: 1 ~ 100
- **설명**: ATR 계산에 사용할 봉의 개수
- **추천**:
  - 단기: 7~10
  - 중기: 14 (기본)
  - 장기: 21~28

### multiplier (ATR 배수)
- **기본값**: 2.0
- **범위**: 0.1 ~ 10.0
- **설명**: ATR 값에 곱하는 배수
- **추천**:
  - 보수적 (좁은 손절): 1.0 ~ 1.5
  - 표준: 2.0 (기본)
  - 공격적 (넓은 손절): 2.5 ~ 3.0

## 사용 예시

### 예시 1: 표준 ATR 기반 손절
```json
{
  "indicators": [
    {
      "id": "atr_14",
      "type": "atr",
      "params": { "period": 14 }
    }
  ],
  "stop_loss": {
    "type": "atr_based",
    "atr_indicator_id": "atr_14",
    "multiplier": 2.0
  }
}
```

**계산 예시**:
- Entry: 50,000
- ATR(14): 500
- Multiplier: 2.0
- LONG SL: 50,000 - (500 × 2.0) = **49,000**
- SHORT SL: 50,000 + (500 × 2.0) = **51,000**

### 예시 2: 보수적 손절 (좁은 스탑)
```json
{
  "stop_loss": {
    "type": "atr_based",
    "atr_indicator_id": "atr_14",
    "multiplier": 1.5
  }
}
```

**계산 예시**:
- Entry: 50,000
- ATR(14): 500
- Multiplier: 1.5
- LONG SL: 50,000 - (500 × 1.5) = **49,250**

### 예시 3: 공격적 손절 (넓은 스탑)
```json
{
  "stop_loss": {
    "type": "atr_based",
    "atr_indicator_id": "atr_14",
    "multiplier": 3.0
  }
}
```

**계산 예시**:
- Entry: 50,000
- ATR(14): 500
- Multiplier: 3.0
- LONG SL: 50,000 - (500 × 3.0) = **48,500**

## Fixed Percent vs ATR Based 비교

| 항목 | Fixed Percent | ATR Based |
|------|---------------|-----------|
| **손절선** | 고정 (진입가의 %) | 동적 (ATR × Multiplier) |
| **변동성 대응** | ❌ 시장 변동성 무시 | ✅ 변동성에 따라 조정 |
| **사용 난이도** | 쉬움 | 보통 |
| **설정 필요** | Percent만 | ATR 지표 + Multiplier |
| **적합한 시장** | 안정적 시장 | 변동성 큰 시장 |

### 장점

#### Fixed Percent
- ✅ 단순하고 이해하기 쉬움
- ✅ 예측 가능한 손실폭
- ✅ 설정이 간단

#### ATR Based
- ✅ 시장 변동성에 자동 적응
- ✅ 변동성 큰 시장에서 너무 빈번한 손절 방지
- ✅ 변동성 작은 시장에서 적절한 손절 거리 유지
- ✅ 전문적인 트레이더들이 선호

### 단점

#### Fixed Percent
- ❌ 시장 변동성 무시
- ❌ 변동성 큰 시장에서 잦은 손절
- ❌ 변동성 작은 시장에서 과도한 손절 거리

#### ATR Based
- ❌ 추가 지표 설정 필요
- ❌ ATR 계산에 warm-up 기간 필요
- ❌ Multiplier 조정 필요

## 실전 전략 예시

### 전략: "ATR 기반 EMA 크로스"
**파일**: `docs/examples/strategy_with_atr_stop_loss.json`

```json
{
  "name": "ATR 기반 손절 EMA 크로스 전략",
  "indicators": [
    {
      "id": "ema_fast",
      "type": "ema",
      "params": { "source": "close", "period": 12 }
    },
    {
      "id": "ema_slow",
      "type": "ema",
      "params": { "source": "close", "period": 26 }
    },
    {
      "id": "atr_14",
      "type": "atr",
      "params": { "period": 14 }
    }
  ],
  "entry": {
    "long": {
      "and": [
        {
          "left": { "ref": "ema_fast" },
          "op": "cross_above",
          "right": { "ref": "ema_slow" }
        }
      ]
    },
    "short": {
      "and": [
        {
          "left": { "ref": "ema_fast" },
          "op": "cross_below",
          "right": { "ref": "ema_slow" }
        }
      ]
    }
  },
  "stop_loss": {
    "type": "atr_based",
    "atr_indicator_id": "atr_14",
    "multiplier": 2.0
  }
}
```

**전략 설명**:
- **진입**: EMA 빠른선이 느린선을 돌파할 때
- **손절**: ATR(14)의 2배 거리
- **장점**: 변동성에 따라 손절 거리 자동 조정

## 프론트엔드 UI 지원

### Step 1: 지표 선택
프론트엔드는 이미 ATR 지표를 완벽하게 지원합니다:

```typescript
{
  type: 'atr',
  name: 'ATR (평균 진폭)',
  category: 'Volatility',
  icon: BarChart3,
  description: '가격 변동성을 측정하는 지표',
  defaultParams: { period: 14 }
}
```

### Step 3: 손절 방식 선택
ATR 기반 손절 UI 기능:
- ✅ ATR 지표 자동 필터링
- ✅ ATR 지표 없으면 비활성화 및 경고
- ✅ ATR 지표 선택 드롭다운
- ✅ Multiplier 입력 (0.1 ~ 10.0)
- ✅ 실시간 설명 및 안내

## 에러 처리

### ATR 지표가 없는 경우
```python
if not atr_indicator_id:
    logger.error("ATR 기반 손절에는 atr_indicator_id가 필요합니다")
    return None
```

### ATR 값을 가져올 수 없는 경우
```python
try:
    atr_value = self.indicator_calc.get_value(atr_indicator_id, bar_index)
except ValueError as e:
    logger.error(f"ATR 지표 값을 가져올 수 없습니다: {e}")
    return None
```

### ATR 값이 0 이하인 경우
```python
if atr_value <= 0:
    logger.warning(f"ATR 값이 0 이하입니다: {atr_value}, 진입 스킵")
    return None
```

## 변경된 파일 목록

### Core Files
- ✅ `engine/utils/indicators.py` - ATR 계산 메서드 추가
- ✅ `engine/utils/strategy_parser.py` - ATR 지표 타입 및 손절가 계산

### Test Files
- ✅ `tests/test_atr_stop_loss.py` - ATR 테스트 (5개 케이스)

### Documentation
- ✅ `docs/ATR_Stop_Loss_Implementation_Summary.md` - 구현 요약
- ✅ `docs/examples/strategy_with_atr_stop_loss.json` - 예제 전략

### Frontend (기존 지원)
- ✅ `apps/web/app/strategies/builder/components/Step1_IndicatorSelector.tsx`
- ✅ `apps/web/app/strategies/builder/components/Step3_StopLossSelector.tsx`
- ✅ `apps/web/types/strategy-draft.ts`

## 테스트 명령어

### Backend 테스트
```bash
cd /home/wonbbo/algoforge
python tests\test_atr_stop_loss.py
```

### Frontend 테스트
```bash
cd apps/web
pnpm test
```

## 결론

ATR 기반 손절 기능이 성공적으로 구현되었습니다!

### 주요 성과
- ✅ ATR 지표 계산 (True Range → ATR)
- ✅ ATR 기반 손절가 동적 계산
- ✅ LONG/SHORT 양방향 지원
- ✅ 다양한 Multiplier 지원
- ✅ 완전한 에러 처리
- ✅ 모든 테스트 통과 (5/5)
- ✅ 프론트엔드 UI 완벽 지원

### 사용자 혜택
💡 이제 사용자는:
- **시장 변동성에 자동 적응하는 손절**
- **변동성 큰 시장에서 안정적인 운영**
- **전문 트레이더 수준의 리스크 관리**
- **UI에서 쉽게 설정 가능**

**ATR 기반 손절 구현 완료!** 🎉

