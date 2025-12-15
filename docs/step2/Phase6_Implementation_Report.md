# Phase 6 구현 보고서: 고급 기능 및 UI 개선

**작성일**: 2025-12-13  
**버전**: 1.0  
**상태**: ✅ 완료

---

## 📋 목차

1. [개요](#1-개요)
2. [구현 목표](#2-구현-목표)
3. [구현 내용](#3-구현-내용)
4. [신규 파일 목록](#4-신규-파일-목록)
5. [수정된 파일 목록](#5-수정된-파일-목록)
6. [주요 기능 상세](#6-주요-기능-상세)
7. [Validation 규칙 강화](#7-validation-규칙-강화)
8. [테스트 결과](#8-테스트-결과)
9. [사용자 가이드](#9-사용자-가이드)
10. [기술적 세부사항](#10-기술적-세부사항)
11. [알려진 제약사항](#11-알려진-제약사항)
12. [향후 개선 사항](#12-향후-개선-사항)
13. [결론](#13-결론)

---

## 1. 개요

### 1.1 Phase 6의 목적

Phase 6는 **AlgoForge Strategy Builder의 고급 기능 구현**을 목표로 합니다.

- Reverse(반대 방향 진입) 설정 UI
- Hook(진입 필터) 설정 UI (MVP에서는 비활성화)
- 지표 ID 편집 기능
- Validation 규칙 강화

### 1.2 구현 범위

```
[Phase 6 범위]
├─ Advanced 설정 컴포넌트
│  ├─ Reverse 설정
│  ├─ Hook 설정 (v2 예정)
│  └─ 통합 UI
├─ 지표 ID 편집기
│  ├─ 인라인 편집
│  ├─ 유효성 검사
│  └─ 중복 체크
└─ Validation 강화
   ├─ ID 형식 검증
   ├─ 지표 참조 검증
   └─ 에러 메시지 개선
```

### 1.3 참조 문서

- `AlgoForge_Strategy_Builder_Implementation_Guide_v1.0.md` (Phase 6 섹션)
- `trading-model-rules.mdc` (Reverse 규칙)
- `backtest-engine-rules.mdc` (TP1 및 Reverse 처리)

---

## 2. 구현 목표

### 2.1 핵심 목표

| 목표 | 설명 | 상태 |
|------|------|------|
| **Reverse 설정** | 반대 방향 진입 활성화/비활성화 | ✅ 완료 |
| **Hook 설정** | 진입 필터 UI (MVP 비활성화) | ✅ 완료 |
| **ID 편집** | 지표 ID 인라인 편집 기능 | ✅ 완료 |
| **Validation 강화** | ID 형식 및 참조 검증 | ✅ 완료 |
| **사용자 경험** | 직관적이고 명확한 UI | ✅ 완료 |

### 2.2 비기능 요구사항

- ✅ **결정성 보장**: 동일 Draft → 동일 Strategy JSON
- ✅ **PRD/TRD 준수**: 모든 규칙 준수
- ✅ **타입 안정성**: TypeScript strict mode
- ✅ **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- ✅ **접근성**: 키보드 네비게이션 지원

---

## 3. 구현 내용

### 3.1 한눈에 보기

| 항목 | 내용 |
|------|------|
| **신규 파일** | 5개 |
| **수정 파일** | 3개 |
| **총 코드 라인** | ~650줄 |
| **새 컴포넌트** | 5개 |
| **UI 개선** | 3개 영역 |

### 3.2 구현 단계

```
Phase 6 구현 단계
├─ Step 1: Advanced 컴포넌트 구조 설계 ✅
├─ Step 2: Reverse 설정 컴포넌트 구현 ✅
├─ Step 3: Hook 설정 컴포넌트 구현 ✅
├─ Step 4: ID 편집기 구현 ✅
├─ Step 5: StepWizard 통합 ✅
├─ Step 6: Validation 규칙 강화 ✅
├─ Step 7: 테스트 및 디버깅 ✅
└─ Step 8: 문서화 ✅
```

---

## 4. 신규 파일 목록

### 4.1 컴포넌트 파일

```
apps/web/app/strategies/builder/components/
├─ Step4_Advanced.tsx                    ✨ 신규 (120줄)
├─ ReverseSettings.tsx                   ✨ 신규 (100줄)
├─ HookSettings.tsx                      ✨ 신규 (110줄)
└─ IndicatorIdEditor.tsx                 ✨ 신규 (160줄)

apps/web/components/ui/
└─ switch.tsx                            ✨ 신규 (60줄)
```

### 4.2 파일 설명

#### Step4_Advanced.tsx
```typescript
/**
 * Step 4: 고급 설정 컴포넌트
 * 
 * Reverse 및 Hook 설정을 통합하는 메인 컴포넌트
 */
```

**주요 기능**:
- Reverse 및 Hook 설정 통합
- 안내 메시지 표시
- 설정 가이드 제공

#### ReverseSettings.tsx
```typescript
/**
 * Reverse 설정 컴포넌트
 * 
 * 반대 방향 진입 설정을 관리
 */
```

**주요 기능**:
- Reverse 활성화/비활성화 스위치
- 동작 모드 표시 (use_entry_opposite)
- 동작 예시 및 설명
- 권장 설정 안내

#### HookSettings.tsx
```typescript
/**
 * Hook 설정 컴포넌트
 * 
 * 진입 필터(Hook) 설정을 관리 (MVP 비활성화)
 */
```

**주요 기능**:
- Hook 개념 설명
- v2 지원 예정 안내
- 예시 필터 목록 표시
- 제약 사항 명시

#### IndicatorIdEditor.tsx
```typescript
/**
 * 지표 ID 수정 컴포넌트
 * 
 * 지표의 ID를 수정할 수 있는 인라인 편집기
 */
```

**주요 기능**:
- 인라인 ID 편집
- 실시간 유효성 검사
- 중복 체크
- 키보드 단축키 (Enter/Esc)

#### switch.tsx
```typescript
/**
 * Switch 컴포넌트
 * 
 * ON/OFF 토글 스위치
 */
```

**주요 기능**:
- 간단한 토글 스위치
- 접근성 지원 (role="switch")
- 비활성화 상태 지원

---

## 5. 수정된 파일 목록

### 5.1 주요 수정 사항

```
apps/web/app/strategies/builder/components/
├─ StepWizard.tsx                        🔧 수정 (Advanced 통합)
├─ Step1_IndicatorSelector.tsx           🔧 수정 (ID 편집기 추가)

apps/web/lib/
└─ draft-validation.ts                   🔧 수정 (ID 검증 강화)
```

### 5.2 수정 내용

#### StepWizard.tsx

**변경 전**:
```typescript
<TabsContent value="advanced">
  {/* 기본 Reverse/Hook 설정 */}
</TabsContent>
```

**변경 후**:
```typescript
<TabsContent value="advanced">
  <Step4_Advanced
    draft={draft}
    onUpdateReverse={(reverse) => {
      updateDraft(d => ({ ...d, reverse }));
    }}
    onUpdateHook={(hook) => {
      updateDraft(d => ({ ...d, hook }));
    }}
  />
</TabsContent>
```

**이유**: 고급 설정을 별도 컴포넌트로 분리하여 유지보수성 향상

#### Step1_IndicatorSelector.tsx

**변경 전**:
```typescript
<span className="font-mono text-sm font-semibold text-primary">
  {indicator.id}
</span>
```

**변경 후**:
```typescript
<IndicatorIdEditor
  currentId={indicator.id}
  existingIds={indicators.map(i => i.id)}
  onUpdate={(newId) => {
    const updated: IndicatorDraft = {
      ...indicator,
      id: newId
    };
    onUpdateIndicator(indicator.id, updated);
  }}
/>
```

**이유**: 지표 ID 편집 기능 추가

#### draft-validation.ts

**추가된 검증**:
```typescript
// ID 형식 검증
for (const indicator of draft.indicators) {
  // 빈 ID 체크
  if (!indicator.id.trim()) {
    errors.push({
      field: 'indicators',
      message: '지표 ID는 필수입니다'
    });
  }
  
  // 영문, 숫자, 언더스코어만 허용
  if (!/^[a-zA-Z0-9_]+$/.test(indicator.id)) {
    errors.push({
      field: 'indicators',
      message: `지표 ID '${indicator.id}'는 영문, 숫자, 언더스코어(_)만 사용 가능합니다`
    });
  }
  
  // 숫자로 시작하지 않도록
  if (/^\d/.test(indicator.id)) {
    errors.push({
      field: 'indicators',
      message: `지표 ID '${indicator.id}'는 숫자로 시작할 수 없습니다`
    });
  }
}
```

**이유**: ID 형식 규칙 강제 및 명확한 에러 메시지 제공

---

## 6. 주요 기능 상세

### 6.1 Reverse 설정

#### 6.1.1 개념

**Reverse**는 포지션 보유 중 반대 방향 진입 신호가 발생했을 때의 동작을 정의합니다.

```
[Reverse 활성화]
롱 포지션 보유 중 → 숏 진입 신호 발생
→ 롱 청산 후 숏 진입

[Reverse 비활성화]
롱 포지션 보유 중 → 숏 진입 신호 발생
→ 신호 무시, 롱 포지션 유지
```

#### 6.1.2 UI 구성

```typescript
<ReverseSettings
  reverse={draft.reverse}
  onUpdate={(reverse) => {
    updateDraft(d => ({ ...d, reverse }));
  }}
/>
```

**구성 요소**:
1. **활성화 스위치**: ON/OFF 토글
2. **동작 모드 표시**: `use_entry_opposite`
3. **동작 예시**: 롱↔숏 전환 시나리오
4. **권장 설정**: 트렌드 추종 전략에 유용

#### 6.1.3 동작 규칙

| 상황 | Reverse ON | Reverse OFF |
|------|-----------|-------------|
| 롱 보유 중 숏 신호 | 롱 청산 → 숏 진입 | 신호 무시 |
| 숏 보유 중 롱 신호 | 숏 청산 → 롱 진입 | 신호 무시 |
| TP1 발생 봉 | Reverse 평가 안 함 | - |

**중요**: TP1 발생 봉에서는 Reverse 신호를 평가하지 않습니다. (부분 청산 직후 즉시 재진입 방지)

### 6.2 Hook 설정

#### 6.2.1 개념

**Hook**은 진입 조건이 만족되더라도 추가 필터를 적용하여 진입을 허용/차단하는 기능입니다.

```
[Hook 예시 - v2에서 구현 예정]
진입 조건 만족 → Hook 평가
├─ 볼륨 필터: 거래량 > 평균 * 1.5
├─ 변동성 필터: ATR 범위 내
└─ 시간대 필터: 특정 시간대만
    ↓
    모두 통과 → 진입 허용
    하나라도 실패 → 진입 차단
```

#### 6.2.2 UI 구성

```typescript
<HookSettings
  hook={draft.hook}
  onUpdate={(hook) => {
    updateDraft(d => ({ ...d, hook }));
  }}
/>
```

**구성 요소**:
1. **활성화 스위치**: 비활성화됨 (MVP)
2. **v2 안내**: 향후 지원 예정 메시지
3. **Hook 개념 설명**: 진입 필터 역할
4. **예시 필터 목록**: 볼륨, 변동성, 시간대 등
5. **제약 사항**: 가격·사이즈·SL/TP 조작 불가

#### 6.2.3 MVP 제약

```typescript
// MVP에서는 Hook 비활성화
<Switch
  id="hook-enabled"
  checked={hook.enabled}
  disabled={true}  // 비활성화
/>
```

**이유**: MVP 범위 외, v2에서 구현 예정

### 6.3 지표 ID 편집기

#### 6.3.1 기능

사용자가 자동 생성된 지표 ID를 원하는 이름으로 변경할 수 있습니다.

```
[자동 생성]
ema_1, ema_2, rsi_1

[사용자 편집]
ema_fast, ema_slow, rsi_main
```

#### 6.3.2 UI 플로우

```
[표시 모드]
ema_1 [편집 아이콘]
    ↓ 클릭
[편집 모드]
[입력 필드: ema_fast] [✓] [✗]
    ↓ Enter 또는 ✓ 클릭
[검증]
├─ 형식 검사 (영문, 숫자, _)
├─ 중복 검사
└─ 숫자 시작 검사
    ↓ 통과
[저장 완료]
ema_fast [편집 아이콘]
```

#### 6.3.3 유효성 검사

```typescript
// ID 검증 규칙
const validateId = (id: string): string | null => {
  // 1. 빈 문자열 체크
  if (!id.trim()) {
    return 'ID는 필수입니다';
  }
  
  // 2. 영문, 숫자, 언더스코어만 허용
  if (!/^[a-zA-Z0-9_]+$/.test(id)) {
    return 'ID는 영문, 숫자, 언더스코어(_)만 사용 가능합니다';
  }
  
  // 3. 숫자로 시작하지 않도록
  if (/^\d/.test(id)) {
    return 'ID는 숫자로 시작할 수 없습니다';
  }
  
  // 4. 중복 체크
  if (id !== currentId && existingIds.includes(id)) {
    return `ID "${id}"는 이미 사용 중입니다`;
  }
  
  return null;
};
```

#### 6.3.4 키보드 단축키

| 키 | 동작 |
|----|------|
| **Enter** | 저장 |
| **Esc** | 취소 |

---

## 7. Validation 규칙 강화

### 7.1 추가된 검증

#### 7.1.1 지표 ID 형식 검증

```typescript
// 기존: 중복 체크만
const uniqueIds = new Set(indicatorIds);
if (indicatorIds.length !== uniqueIds.size) {
  errors.push({ 
    field: 'indicators', 
    message: '지표 ID가 중복되었습니다' 
  });
}

// 추가: 형식 검증
for (const indicator of draft.indicators) {
  // 빈 ID
  if (!indicator.id.trim()) {
    errors.push({
      field: 'indicators',
      message: '지표 ID는 필수입니다'
    });
  }
  
  // 형식 검사
  if (!/^[a-zA-Z0-9_]+$/.test(indicator.id)) {
    errors.push({
      field: 'indicators',
      message: `지표 ID '${indicator.id}'는 영문, 숫자, 언더스코어(_)만 사용 가능합니다`
    });
  }
  
  // 숫자 시작 금지
  if (/^\d/.test(indicator.id)) {
    errors.push({
      field: 'indicators',
      message: `지표 ID '${indicator.id}'는 숫자로 시작할 수 없습니다`
    });
  }
}
```

### 7.2 검증 규칙 전체 목록

| 항목 | 규칙 | 에러 메시지 |
|------|------|------------|
| **전략 이름** | 필수, 공백 불가 | "전략 이름은 필수입니다" |
| **지표 ID** | 필수 | "지표 ID는 필수입니다" |
| **지표 ID 형식** | 영문, 숫자, _ | "영문, 숫자, 언더스코어(_)만 사용 가능합니다" |
| **지표 ID 시작** | 숫자로 시작 불가 | "숫자로 시작할 수 없습니다" |
| **지표 ID 중복** | 중복 불가 | "지표 ID가 중복되었습니다" |
| **진입 조건** | 롱 또는 숏 최소 1개 | "롱 또는 숏 진입 조건이 최소 1개 필요합니다" |
| **조건 좌변** | 필수 | "조건의 좌변이 비어있습니다" |
| **조건 우변** | 필수 | "조건의 우변이 비어있습니다" |
| **cross 연산자** | 양쪽 모두 지표 | "cross 연산자는 양쪽 모두 지표여야 합니다" |
| **지표 참조** | 존재하는 지표 | "지표 '{id}'를 찾을 수 없습니다" |
| **손절** | 필수 | "손절 방식은 필수입니다" |
| **ATR 기반 SL** | ATR 지표 존재 | "ATR 지표를 먼저 추가해야 합니다" |
| **손절 비율** | 0 < percent ≤ 100 | "손절 비율은 0보다 크고 100 이하여야 합니다" |

---

## 8. 테스트 결과

### 8.1 빌드 테스트

```bash
cd apps/web
pnpm build
```

**결과**: ✅ 성공

```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Generating static pages (8/8)
✓ Finalizing page optimization
```

### 8.2 TypeScript 타입 체크

```bash
pnpm tsc --noEmit
```

**결과**: ✅ 타입 에러 없음

### 8.3 Lint 체크

```bash
pnpm lint
```

**결과**: ✅ Lint 에러 없음

### 8.4 기능 테스트

#### 테스트 시나리오 1: Reverse 설정 ✅

**단계**:
1. Strategy Builder 페이지 접속
2. "고급" 탭 클릭
3. Reverse 스위치 ON/OFF 토글
4. 동작 모드 및 예시 확인

**결과**: ✅ 정상 작동

#### 테스트 시나리오 2: Hook 설정 (비활성화) ✅

**단계**:
1. "고급" 탭에서 Hook 섹션 확인
2. 스위치가 비활성화되어 있는지 확인
3. v2 안내 메시지 확인

**결과**: ✅ 정상 작동

#### 테스트 시나리오 3: 지표 ID 편집 ✅

**단계**:
1. Step 1에서 EMA 지표 추가
2. 자동 생성된 ID (ema_1) 옆 편집 아이콘 클릭
3. "ema_fast"로 변경 후 Enter
4. 저장 확인

**결과**: ✅ 정상 작동

#### 테스트 시나리오 4: ID 유효성 검사 ✅

**테스트 케이스**:
- ❌ 빈 ID → "ID는 필수입니다"
- ❌ "123_ema" → "숫자로 시작할 수 없습니다"
- ❌ "ema-fast" → "영문, 숫자, 언더스코어(_)만 사용 가능합니다"
- ❌ 중복 ID → "ID는 이미 사용 중입니다"
- ✅ "ema_fast" → 저장 성공

**결과**: ✅ 모든 케이스 정상 작동

#### 테스트 시나리오 5: JSON 생성 ✅

**단계**:
1. Reverse 활성화
2. JSON Preview 확인

**기대 결과**:
```json
{
  "reverse": {
    "enabled": true,
    "mode": "use_entry_opposite"
  }
}
```

**결과**: ✅ 정확히 생성됨

---

## 9. 사용자 가이드

### 9.1 Reverse 설정 방법

#### Step 1: 고급 탭 이동
```
Strategy Builder → 고급 탭 클릭
```

#### Step 2: Reverse 활성화
```
Reverse 섹션 → 스위치 ON
```

#### Step 3: 동작 확인
- 동작 모드: `use_entry_opposite`
- 예시: 롱 보유 중 숏 신호 → 롱 청산 후 숏 진입

#### Step 4: 권장 설정
- **트렌드 추종 전략**: Reverse 활성화 권장
- **레인지 전략**: Reverse 비활성화 권장
- **백테스트로 확인**: 전략 특성에 맞게 조정

### 9.2 지표 ID 편집 방법

#### Step 1: 지표 추가
```
Step 1: 지표 선택 → EMA 추가
자동 생성 ID: ema_1
```

#### Step 2: ID 편집
```
ema_1 옆 편집 아이콘 클릭
→ 입력 필드에 새 ID 입력 (예: ema_fast)
→ Enter 또는 ✓ 클릭
```

#### Step 3: 유효성 검사
- ✅ 영문, 숫자, 언더스코어만 사용
- ✅ 숫자로 시작하지 않음
- ✅ 중복되지 않음

#### Step 4: 저장 완료
```
새 ID: ema_fast
→ 진입 조건에서 ema_fast 사용 가능
```

### 9.3 ID 네이밍 가이드

#### 권장 네이밍 패턴

```typescript
// 좋은 예
ema_fast          // 명확한 의미
ema_slow          // 역할 표시
rsi_main          // 주요 지표
atr_volatility    // 용도 표시

// 나쁜 예
123_ema           // 숫자로 시작
ema-fast          // 하이픈 사용
ema fast          // 공백 사용
emaFast           // camelCase (권장하지 않음)
```

#### 네이밍 컨벤션

1. **snake_case 사용**: `ema_fast`, `rsi_main`
2. **의미 있는 이름**: `fast`, `slow`, `main`, `signal`
3. **일관성 유지**: 모든 지표에 동일한 패턴 적용

---

## 10. 기술적 세부사항

### 10.1 컴포넌트 구조

```
Step4_Advanced (메인)
├─ ReverseSettings
│  ├─ Switch (토글)
│  ├─ Alert (안내)
│  └─ 동작 예시
└─ HookSettings
   ├─ Switch (비활성화)
   ├─ Alert (v2 안내)
   └─ Hook 개념 설명
```

### 10.2 상태 관리

```typescript
// Draft State
interface StrategyDraft {
  // ...
  reverse: ReverseDraft;
  hook: HookDraft;
}

// Reverse Draft
type ReverseDraft = 
  | { enabled: false }
  | { enabled: true; mode: 'use_entry_opposite' };

// Hook Draft
interface HookDraft {
  enabled: boolean;
}
```

### 10.3 데이터 흐름

```
[사용자 입력]
    ↓
[Draft State 업데이트]
    ↓
[실시간 Validation]
    ↓
[JSON Preview 자동 생성]
    ↓
[저장 → API 전송]
```

### 10.4 ID 편집 로직

```typescript
// 1. 편집 시작
const handleStartEdit = () => {
  setIsEditing(true);
  setNewId(currentId);
};

// 2. 유효성 검사
const validateId = (id: string): string | null => {
  // 검증 로직
};

// 3. 저장
const handleSave = () => {
  const error = validateId(newId);
  if (error) {
    setError(error);
    return;
  }
  onUpdate(newId);
  setIsEditing(false);
};
```

### 10.5 Switch 컴포넌트

```typescript
export function Switch({
  checked = false,
  onCheckedChange,
  disabled = false
}: SwitchProps) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onCheckedChange?.(!checked)}
      className={`
        ${checked ? 'bg-primary' : 'bg-input'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      <span className={`
        ${checked ? 'translate-x-6' : 'translate-x-0.5'}
      `} />
    </button>
  );
}
```

---

## 11. 알려진 제약사항

### 11.1 MVP 제약

| 항목 | 제약 | 해결 계획 |
|------|------|----------|
| **Hook** | 비활성화 | v2에서 구현 |
| **Reverse 커스텀** | use_entry_opposite만 | v2에서 커스텀 조건 추가 |
| **ID 일괄 변경** | 개별 편집만 | v2에서 일괄 편집 기능 |

### 11.2 브라우저 호환성

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### 11.3 접근성

- ✅ 키보드 네비게이션
- ✅ 스크린 리더 지원 (role, aria-*)
- ⚠️ 색상 대비 개선 필요 (일부 Alert)

---

## 12. 향후 개선 사항

### 12.1 v2 계획

#### Hook 기능 구현
```typescript
// v2에서 구현 예정
interface HookDraft {
  enabled: boolean;
  filters: HookFilter[];
}

interface HookFilter {
  type: 'volume' | 'volatility' | 'time' | 'trend';
  condition: any;
}
```

#### Reverse 커스텀 조건
```typescript
// v2에서 구현 예정
type ReverseDraft = 
  | { enabled: false }
  | { enabled: true; mode: 'use_entry_opposite' }
  | { enabled: true; mode: 'custom'; custom_conditions: ConditionDraft[] };
```

### 12.2 UI 개선

- [ ] ID 일괄 변경 기능
- [ ] 지표 복제 기능
- [ ] 지표 순서 변경 (드래그 앤 드롭)
- [ ] 전략 템플릿 저장/불러오기
- [ ] 다크 모드 최적화

### 12.3 Validation 개선

- [ ] 실시간 지표 참조 검증
- [ ] 순환 참조 감지
- [ ] 경고(Warning) 레벨 추가
- [ ] 성능 최적화 제안

---

## 13. 결론

### 13.1 달성한 목표

| 목표 | 상태 | 비고 |
|------|------|------|
| Reverse 설정 UI | ✅ 완료 | 직관적이고 명확함 |
| Hook 설정 UI | ✅ 완료 | v2 안내 포함 |
| ID 편집 기능 | ✅ 완료 | 유효성 검사 완벽 |
| Validation 강화 | ✅ 완료 | ID 형식 검증 추가 |
| 빌드 성공 | ✅ 완료 | 타입 에러 없음 |

### 13.2 코드 품질

- ✅ **타입 안정성**: TypeScript strict mode
- ✅ **컴포넌트 분리**: 단일 책임 원칙
- ✅ **재사용성**: Switch, Alert 등 공통 컴포넌트
- ✅ **문서화**: 모든 컴포넌트에 docstring
- ✅ **한글 주석**: 복잡한 로직 설명

### 13.3 사용자 가치

```
[Before Phase 6]
- Reverse 설정 불가
- ID 편집 불가
- 형식 검증 미흡

[After Phase 6]
✅ Reverse 설정 가능
✅ ID 자유롭게 편집
✅ 명확한 에러 메시지
✅ 직관적인 UI
```

### 13.4 다음 단계

Phase 6 완료로 **Strategy Builder의 핵심 기능이 모두 구현**되었습니다.

**준비된 것**:
- ✅ 지표 선택 및 설정
- ✅ 진입 조건 구성
- ✅ 손절 방식 선택
- ✅ Reverse 설정
- ✅ ID 편집
- ✅ Validation
- ✅ JSON 생성

**다음 Phase (선택)**:
- Phase 7: 전략 테스트 및 최적화
- Phase 8: 전략 비교 및 분석
- Phase 9: 전략 템플릿 및 공유

---

## 부록 A: 파일 구조

```
apps/web/
├─ app/strategies/builder/
│  ├─ page.tsx
│  └─ components/
│     ├─ StrategyHeader.tsx
│     ├─ StepWizard.tsx                 🔧 수정
│     ├─ Step1_IndicatorSelector.tsx    🔧 수정
│     ├─ Step2_EntryBuilder.tsx
│     ├─ Step3_StopLossSelector.tsx
│     ├─ Step4_Advanced.tsx             ✨ 신규
│     ├─ ReverseSettings.tsx            ✨ 신규
│     ├─ HookSettings.tsx               ✨ 신규
│     ├─ IndicatorIdEditor.tsx          ✨ 신규
│     ├─ ConditionRow.tsx
│     └─ JsonPreviewPanel.tsx
├─ components/ui/
│  ├─ switch.tsx                        ✨ 신규
│  ├─ alert.tsx
│  ├─ button.tsx
│  ├─ card.tsx
│  └─ ...
└─ lib/
   ├─ draft-validation.ts               🔧 수정
   ├─ draft-to-json.ts
   └─ strategy-draft-utils.ts
```

---

## 부록 B: 코드 예시

### Reverse 설정 사용 예시

```typescript
// Draft State
const draft: StrategyDraft = {
  name: "EMA Cross Strategy",
  // ...
  reverse: {
    enabled: true,
    mode: 'use_entry_opposite'
  }
};

// JSON 변환 결과
{
  "schema_version": "1.0",
  "meta": {
    "name": "EMA Cross Strategy"
  },
  // ...
  "reverse": {
    "enabled": true,
    "mode": "use_entry_opposite"
  }
}
```

### ID 편집 사용 예시

```typescript
// 1. 지표 추가 (자동 ID)
const indicator: IndicatorDraft = {
  id: "ema_1",  // 자동 생성
  type: "ema",
  params: { source: "close", period: 20 }
};

// 2. ID 편집
<IndicatorIdEditor
  currentId="ema_1"
  existingIds={["rsi_1", "atr_1"]}
  onUpdate={(newId) => {
    // newId = "ema_fast"
    updateIndicator("ema_1", { ...indicator, id: newId });
  }}
/>

// 3. 편집 후
const updatedIndicator: IndicatorDraft = {
  id: "ema_fast",  // 사용자가 편집
  type: "ema",
  params: { source: "close", period: 20 }
};
```

---

**작성일**: 2025-12-13  
**작성자**: Cursor AI  
**버전**: 1.0  
**상태**: ✅ 완료

