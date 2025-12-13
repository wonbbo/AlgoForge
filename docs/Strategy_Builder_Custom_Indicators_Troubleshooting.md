# 전략 빌더 커스텀 지표 문제 해결

## 문제: 커스텀 지표가 나타나지 않음

### 원인
`IndicatorDraft` 타입이 고정된 리터럴 타입으로 제한되어 있었습니다:

```typescript
// 문제가 있던 코드
type: 'ema' | 'sma' | 'rsi' | 'atr' | 'price' | 'candle';
```

이로 인해 커스텀 지표 타입 (예: `custom_volume`, `my_macd`)을 할당할 수 없었습니다.

### 해결 방법

**파일**: `apps/web/types/strategy-draft.ts`

```typescript
// 수정된 코드
export interface IndicatorDraft {
  id: string;
  type: string;  // ✅ 모든 지표 타입 허용
  params: Record<string, any>;
}
```

## 확인 방법

### 1. API 서버 확인

```bash
curl http://localhost:8000/api/indicators/
```

**기대 결과**: 내장 지표 + 커스텀 지표 JSON 응답

### 2. 데이터베이스 확인

```bash
cd C:\Users\wonbbo\Workspace\Cursor\AlgoForge
python -c "import sqlite3; conn = sqlite3.connect('db/algoforge.db'); cursor = conn.execute('SELECT name, type, implementation_type FROM indicators'); [print(f'{row[0]:20s} | {row[1]:20s} | {row[2]}') for row in cursor.fetchall()]"
```

**기대 결과**:
```
EMA                  | ema                  | builtin
SMA                  | sma                  | builtin
RSI                  | rsi                  | builtin
ATR                  | atr                  | builtin
CustomVolume         | custom_volume        | custom
```

### 3. 브라우저 콘솔 확인

1. 브라우저 개발자 도구 열기 (F12)
2. `/strategies/builder`로 이동
3. Console 탭 확인
4. 네트워크 탭에서 `/api/indicators` 요청 확인

**정상 동작 시**:
- 콘솔 에러 없음
- 네트워크: `200 OK` 응답
- 지표 카드에 커스텀 지표 표시 (커스텀 배지 포함)

**에러 발생 시**:
```
지표 목록 로드 실패: [에러 메시지]
```

## 테스트 시나리오

### 시나리오 1: 커스텀 지표 등록 및 전략 빌더에서 확인

#### Step 1: 커스텀 지표 등록
```bash
# 1. API 서버 시작
cd C:\Users\wonbbo\Workspace\Cursor\AlgoForge
python -m uvicorn apps.api.main:app --reload --port 8000

# 2. Frontend 서버 시작 (다른 터미널)
cd apps/web
pnpm dev
```

#### Step 2: 지표 등록
1. `http://localhost:3000/indicators/new` 접속
2. 테스트 지표 등록:
   - 이름: `Test SMA`
   - 타입: `test_sma`
   - 카테고리: `trend`
   - 코드:
     ```python
     def calculate_test_sma(df, params):
         period = params.get('period', 20)
         return df['close'].rolling(window=period).mean().fillna(0)
     ```
   - 파라미터: `{"period": 20}`
   - 출력 필드: `main`
3. "코드 검증" → "등록"

#### Step 3: 전략 빌더에서 확인
1. `http://localhost:3000/strategies/builder` 접속
2. **Step 1: 지표 선택**에서 확인
3. "Test SMA" 카드 확인 (커스텀 배지 표시)
4. "+" 버튼 클릭하여 추가
5. 파라미터 설정 (period: 20)

### 시나리오 2: 다중 출력 지표 확인

#### Step 1: MACD 스타일 지표 등록
```python
def calculate_test_macd(df, params):
    fast = params.get('fast', 12)
    slow = params.get('slow', 26)
    signal = params.get('signal', 9)
    
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return {
        'main': macd_line.fillna(0),
        'signal': signal_line.fillna(0),
        'histogram': histogram.fillna(0)
    }
```

- 출력 필드: `main,signal,histogram`

#### Step 2: 전략 빌더에서 확인
- "Test MACD" 카드에 **"3 출력"** 배지 표시
- 추가 후 Entry Condition에서 참조 가능:
  - `test_macd_1_main`
  - `test_macd_1_signal`
  - `test_macd_1_histogram`

## 추가 개선 사항

### 브라우저 캐싱 문제 해결

브라우저가 이전 데이터를 캐싱하고 있을 수 있습니다:

**해결**:
1. 브라우저 새로고침 (Ctrl + F5 또는 Cmd + Shift + R)
2. 브라우저 캐시 삭제
3. 시크릿 모드에서 테스트

### 개발 서버 재시작

코드 변경 후 개발 서버가 자동으로 재시작되지 않을 수 있습니다:

**해결**:
```bash
# Frontend 서버 재시작
cd apps/web
# Ctrl + C로 중지
pnpm dev
```

### API 응답 로깅 추가

디버깅을 위해 콘솔 로그를 확인할 수 있습니다:

```typescript
// Step1_IndicatorSelector.tsx의 loadIndicators 함수에 이미 포함됨
const loadIndicators = async () => {
  try {
    const data = await indicatorApi.list();
    console.log('✅ 지표 로드 성공:', data.length, '개');
    console.log('커스텀 지표:', data.filter(i => i.implementation_type === 'custom'));
    setAvailableIndicators(data);
  } catch (err: any) {
    console.error('❌ 지표 목록 로드 실패:', err);
    // ...
  }
};
```

## 최종 체크리스트

### Backend 확인
- [ ] API 서버 실행 중 (`http://localhost:8000`)
- [ ] `/api/indicators` 엔드포인트 응답 확인
- [ ] 커스텀 지표가 DB에 등록되어 있음

### Frontend 확인
- [ ] 개발 서버 실행 중 (`http://localhost:3000`)
- [ ] `IndicatorDraft.type`이 `string`으로 변경됨
- [ ] 브라우저 캐시 삭제 및 새로고침

### UI 확인
- [ ] `/strategies/builder` 접속
- [ ] Step 1에서 커스텀 지표 카드 표시 확인
- [ ] "커스텀" 배지 표시 확인
- [ ] "+" 버튼 클릭하여 추가 가능 확인

## 디버깅 팁

### 브라우저 콘솔에서 직접 테스트

```javascript
// 개발자 도구 Console에서 실행
fetch('http://localhost:8000/api/indicators/')
  .then(r => r.json())
  .then(data => {
    console.log('총 지표:', data.total);
    console.log('내장 지표:', data.indicators.filter(i => i.implementation_type === 'builtin'));
    console.log('커스텀 지표:', data.indicators.filter(i => i.implementation_type === 'custom'));
  });
```

### React DevTools로 State 확인

1. React DevTools 설치
2. Components 탭 열기
3. `Step1_IndicatorSelector` 컴포넌트 선택
4. `availableIndicators` state 확인

## 해결 완료!

- ✅ 타입 제약 제거 (`type: string`)
- ✅ `as any` 캐스팅 제거
- ✅ 린터 오류 0개
- ✅ 커스텀 지표 표시 가능

이제 전략 빌더에서 내장 지표와 커스텀 지표가 모두 표시됩니다!

---

**수정 일자**: 2025-12-13  
**영향받는 파일**: 2개
- `apps/web/types/strategy-draft.ts`
- `apps/web/app/strategies/builder/components/Step1_IndicatorSelector.tsx`

