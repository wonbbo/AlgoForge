# 거래 상세 페이지에 매수 규모 표시 추가

## 📝 요청 사항

Run의 거래 목록에서 거래를 선택했을 때 나오는 거래 정보 보기에서:
- 기존: 진입가, 포지션 크기, 초기 리스크 표시
- 추가: **매수 규모** (진입가 × 포지션 크기) 표시

---

## ✅ 구현

### 수정된 파일
- `apps/web/app/runs/[id]/trades/[tradeId]/page.tsx`

### 변경 사항

#### Before (기존 레이아웃)
```tsx
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
  <div>진입 시각</div>
  <div>진입가</div>
  <div>포지션 크기</div>
  <div>초기 리스크</div>
</div>
```

**표시 정보**:
- 진입 시각
- 진입가
- 포지션 크기
- 초기 리스크

---

#### After (개선된 레이아웃)

```tsx
<div className="space-y-4">
  {/* 첫 번째 줄: 기본 정보 */}
  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div>진입 시각</div>
    <div>진입가</div>
    <div>포지션 크기</div>
  </div>
  
  {/* 두 번째 줄: 금액 정보 (강조) */}
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t">
    <div>
      <p className="text-sm text-muted-foreground">매수 규모</p>
      <p className="text-xl font-bold font-mono text-primary">
        {formatCurrency(trade.entry_price * trade.position_size)}
      </p>
      <p className="text-xs text-muted-foreground mt-1">
        진입가 × 포지션 크기
      </p>
    </div>
    <div>
      <p className="text-sm text-muted-foreground">초기 리스크</p>
      <p className="text-xl font-bold text-destructive">
        {formatCurrency(trade.initial_risk)}
      </p>
      <p className="text-xs text-muted-foreground mt-1">
        2% of Initial Balance
      </p>
    </div>
  </div>
</div>
```

**표시 정보** (추가):
- 진입 시각
- 진입가
- 포지션 크기
- ✅ **매수 규모** (신규 추가)
- 초기 리스크

---

## 📊 화면 구성

### 진입 정보 카드

```
┌─────────────────────────────────────────────────┐
│ 진입 정보                                         │
├─────────────────────────────────────────────────┤
│                                                   │
│  [진입 시각]    [진입가]        [포지션 크기]      │
│  2024-01-01    50,000.00       0.5000           │
│  12:00:00                                        │
│                                                   │
│ ─────────────────────────────────────────────── │
│                                                   │
│  [매수 규모] ★                [초기 리스크]       │
│  $25,000.00                   $200.00           │
│  진입가 × 포지션 크기            2% of Initial    │
│                                Balance           │
│                                                   │
└─────────────────────────────────────────────────┘
```

---

## 🎯 주요 특징

### 1. 계산식
```typescript
const entryValue = trade.entry_price * trade.position_size
```

**예시**:
- 진입가: $50,000
- 포지션 크기: 0.5 (계약)
- **매수 규모: $25,000**

---

### 2. 시각적 강조

#### 텍스트 크기
```tsx
// 첫 번째 줄 (기본 정보): 일반 크기
<p className="font-medium">...</p>

// 두 번째 줄 (금액 정보): 크고 굵게
<p className="text-xl font-bold">...</p>
```

#### 색상
```tsx
// 매수 규모: Primary 색상 (강조)
<p className="text-primary">$25,000.00</p>

// 초기 리스크: Destructive 색상 (경고)
<p className="text-destructive">$200.00</p>
```

#### 설명 텍스트
```tsx
// 각 금액 필드에 계산 방법 표시
<p className="text-xs text-muted-foreground mt-1">
  진입가 × 포지션 크기
</p>
```

---

### 3. 레이아웃 개선

#### 반응형 디자인
```tsx
// 모바일: 1열
// 태블릿 이상: 3열 (첫 줄), 2열 (둘째 줄)
<div className="grid grid-cols-1 md:grid-cols-3 gap-4">

<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
```

#### 시각적 구분
```tsx
// 두 섹션을 구분선으로 분리
<div className="... pt-2 border-t">
```

---

## 💡 사용 사례

### 거래 분석 시나리오

#### 1. 포지션 크기 평가
```
매수 규모: $25,000
초기 잔고: $10,000
→ 레버리지: 2.5배
```

#### 2. 리스크 대비 규모
```
매수 규모: $25,000
초기 리스크: $200
→ 리스크 비율: 0.8% (안전)
```

#### 3. 손익률 계산 기준
```
매수 규모: $25,000
총 손익: $500
→ 손익률: 2.0%
```

---

## 🎨 디자인 원칙

### 1. 정보 위계
```
Level 1: 기본 정보 (시간, 가격, 크기)
Level 2: 계산된 금액 (매수 규모, 리스크) ★ 강조
```

### 2. 색상 의미
```
Primary (파란색): 긍정적/주요 정보 (매수 규모)
Destructive (빨간색): 주의/리스크 (초기 리스크)
```

### 3. 가독성
```
- 큰 글씨: 중요한 숫자
- 작은 글씨: 설명 텍스트
- Monospace: 금액/가격 (정렬)
```

---

## 🧪 테스트

### 1. 브라우저 접속
```
http://localhost:3000/runs/{run_id}
```

### 2. 거래 선택
```
거래 목록에서 아무 거래나 클릭
```

### 3. 확인 사항
- ✅ 진입 정보 카드에 5개 필드 표시
- ✅ "매수 규모" 필드가 두 번째 줄 왼쪽에 표시
- ✅ 값이 올바르게 계산됨 (진입가 × 포지션)
- ✅ 금액이 크고 굵게 표시됨
- ✅ 설명 텍스트 "진입가 × 포지션 크기" 표시
- ✅ 모바일에서도 레이아웃 정상

---

## 📱 반응형 동작

### Desktop (md 이상)
```
┌──────────────────────────────────────┐
│  진입시각    진입가      포지션크기    │
│ ──────────────────────────────────── │
│  매수규모              초기리스크      │
└──────────────────────────────────────┘
```

### Mobile (md 미만)
```
┌──────────────┐
│  진입시각     │
├──────────────┤
│  진입가       │
├──────────────┤
│  포지션크기   │
├──────────────┤
│  매수규모     │
├──────────────┤
│  초기리스크   │
└──────────────┘
```

---

## 🎉 완료!

**추가된 기능**:
- ✅ 매수 규모 표시 (진입가 × 포지션 크기)
- ✅ 계산 방법 설명 텍스트
- ✅ 시각적 강조 (크기, 색상)
- ✅ 개선된 레이아웃 (2줄 구성)
- ✅ 반응형 디자인

**효과**:
- 포지션의 실제 금액을 한눈에 파악
- 리스크 대비 규모 비교 용이
- 거래 분석 시 유용한 정보 제공

---

**작성 일자**: 2025-12-13  
**수정 파일**: 1개  
**상태**: 완료 ✅

