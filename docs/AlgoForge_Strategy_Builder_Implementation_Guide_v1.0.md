# AlgoForge 전략 빌더 UI 구현 가이드 v1.0

## 목차
1. [개요 및 목표](#1-개요-및-목표)
2. [절대 준수 사항](#2-절대-준수-사항)
3. [아키텍처 개요](#3-아키텍처-개요)
4. [기술 스택](#4-기술-스택)
5. [Draft State 설계](#5-draft-state-설계)
6. [컴포넌트 구조](#6-컴포넌트-구조)
7. [단계별 구현 가이드](#7-단계별-구현-가이드)
8. [Validation 규칙](#8-validation-규칙)
9. [Draft → JSON 변환 로직](#9-draft--json-변환-로직)
10. [Canonicalization](#10-canonicalization)
11. [테스트 전략](#11-테스트-전략)
12. [구현 체크리스트](#12-구현-체크리스트)

---

## 1. 개요 및 목표

### 1.1 프로젝트 목적
AlgoForge 전략 빌더는 **JSON을 모르는 사용자도 전략을 직관적으로 만들 수 있는** UI를 제공합니다.

### 1.2 핵심 목표
1. **사용자 친화성**: JSON 지식 없이도 전략 작성 가능
2. **결정성 보장**: 동일 Draft → 동일 Strategy JSON → 동일 strategy_hash
3. **규칙 준수**: PRD/TRD의 모든 규칙을 UI 레벨에서 강제
4. **확장성**: 향후 고급 기능 추가 시에도 JSON 구조 유지

### 1.3 사용자 플로우
```
[전략 이름 입력]
    ↓
[Step 1: 지표 선택]
    ↓
[Step 2: 진입 조건 구성]
    ↓
[Step 3: 손절 방식 선택]
    ↓
[Advanced: Reverse/Hook 설정] (선택)
    ↓
[JSON 미리보기]
    ↓
[저장/실행]
```

---

## 2. 절대 준수 사항

### 2.1 금지 사항 (MUST NOT)
❌ **절대 하지 말아야 할 것들**:
1. Strategy JSON Schema v1.0 구조 변경
2. PRD/TRD 규칙 단순화 또는 생략
3. Draft에서 자동 보정 로직 추가 (예: 잘못된 조건 자동 수정)
4. JSON 생성 시 비결정적 요소 추가 (난수, timestamp 등)
5. Validation 규칙 완화

### 2.2 필수 사항 (MUST)
✅ **반드시 지켜야 할 것들**:
1. Draft State는 UI 전용, JSON은 Draft에서만 생성
2. Validation 실패 시 JSON 생성 금지
3. 동일 Draft → 동일 strategy_hash 보장
4. 모든 UI 입력은 명확한 Validation과 에러 메시지
5. JSON Preview는 Read-only

### 2.3 참고 문서 우선순위
```
PRD v1.0 (최우선)
  ↓
TRD v1.0
  ↓
ADR v1.0
  ↓
UI Wireframe
  ↓
UI Component Design
  ↓
Draft to JSON Rules
```

---

## 3. 아키텍처 개요

### 3.1 전체 구조
```
┌─────────────────────────────────────┐
│     Strategy Builder UI             │
├─────────────────────────────────────┤
│  [Draft State]                      │
│    - indicatorsDraft                │
│    - entryDraft                     │
│    - stopLossDraft                  │
│    - reverseDraft                   │
│    - hookDraft                      │
├─────────────────────────────────────┤
│  [Validation Layer]                 │
│    - 실시간 검증                     │
│    - 에러 표시                       │
├─────────────────────────────────────┤
│  [JSON Converter]                   │
│    - Draft → Strategy JSON          │
│    - Canonicalization               │
├─────────────────────────────────────┤
│  [Strategy JSON] (Schema v1.0)      │
└─────────────────────────────────────┘
```

### 3.2 데이터 흐름
```
User Input
    ↓
Draft State Update
    ↓
Real-time Validation
    ↓
JSON Preview 자동 생성
    ↓
사용자 확인
    ↓
저장/실행 → API 전송
```

---

## 4. 기술 스택

### 4.1 Frontend Framework
- **Next.js 14+** (App Router)
- **TypeScript** (strict mode)
- **React 18+**

### 4.2 UI Library
- **ShadCN UI** (컴포넌트)
- **TailwindCSS** (스타일링)
- **Radix UI** (ShadCN 기반)

### 4.3 상태 관리
- **React useState / useReducer** (MVP)
- Context API (필요 시)

### 4.4 Form 관리
- **React Hook Form** (추천)
- **Zod** (스키마 검증)

### 4.5 기타
- **clsx** / **tailwind-merge** (스타일 조합)
- **lucide-react** (아이콘)

---

## 5. Draft State 설계

### 5.1 Draft State 타입 정의

```typescript
// types/strategy-draft.ts

/**
 * 전략 빌더 Draft State
 * 
 * UI 전용 상태로, 최종적으로 Strategy JSON Schema v1.0으로 변환됨
 */
export interface StrategyDraft {
  // 메타 정보
  name: string;
  description: string;
  
  // 지표 (Step 1)
  indicators: IndicatorDraft[];
  
  // 진입 조건 (Step 2)
  entry: EntryDraft;
  
  // 손절 (Step 3)
  stopLoss: StopLossDraft;
  
  // Reverse (Advanced)
  reverse: ReverseDraft;
  
  // Hook (Advanced)
  hook: HookDraft;
}

/**
 * 지표 Draft
 */
export interface IndicatorDraft {
  // 고유 ID (사용자가 중복 불가하게 입력 또는 자동 생성)
  id: string;
  
  // 지표 타입
  type: 'ema' | 'sma' | 'rsi' | 'atr' | 'price' | 'candle';
  
  // 파라미터 (지표 타입에 따라 다름)
  params: Record<string, any>;
}

/**
 * EMA 지표 예시
 */
export interface EMAIndicator {
  id: string;
  type: 'ema';
  params: {
    source: 'close' | 'open' | 'high' | 'low';
    period: number;
  };
}

/**
 * RSI 지표 예시
 */
export interface RSIIndicator {
  id: string;
  type: 'rsi';
  params: {
    source: 'close';
    period: number;
  };
}

/**
 * 진입 조건 Draft
 */
export interface EntryDraft {
  long: {
    conditions: ConditionDraft[];  // AND 조건
  };
  short: {
    conditions: ConditionDraft[];  // AND 조건
  };
}

/**
 * 조건 Draft
 * 
 * 예: "ema_fast" > "ema_slow"
 */
export interface ConditionDraft {
  // 임시 ID (UI 렌더링용)
  tempId: string;
  
  // 좌변
  left: {
    type: 'indicator' | 'number';
    value: string | number;  // indicator면 id, number면 숫자
  };
  
  // 연산자
  operator: '>' | '<' | '>=' | '<=' | 'cross_above' | 'cross_below';
  
  // 우변
  right: {
    type: 'indicator' | 'number';
    value: string | number;
  };
}

/**
 * 손절 Draft
 */
export type StopLossDraft = 
  | { type: 'fixed_percent'; percent: number }
  | { type: 'atr_based'; atr_indicator_id: string; multiplier: number };

/**
 * Reverse Draft
 */
export type ReverseDraft = 
  | { enabled: false }
  | { enabled: true; mode: 'use_entry_opposite' }
  | { enabled: true; mode: 'custom'; custom_conditions: any };  // v2

/**
 * Hook Draft
 */
export interface HookDraft {
  enabled: boolean;
  // Hook 관련 설정 (MVP에서는 OFF 기본)
}
```

### 5.2 초기 Draft State

```typescript
// lib/strategy-draft-utils.ts

/**
 * 빈 Draft State 생성
 */
export function createEmptyDraft(): StrategyDraft {
  return {
    name: '',
    description: '',
    indicators: [],
    entry: {
      long: { conditions: [] },
      short: { conditions: [] }
    },
    stopLoss: { type: 'fixed_percent', percent: 2 },
    reverse: { enabled: true, mode: 'use_entry_opposite' },
    hook: { enabled: false }
  };
}
```

---

## 6. 컴포넌트 구조

### 6.1 컴포넌트 트리
```
app/strategies/builder/page.tsx
  ↓
<StrategyBuilderPage>
  ├─ <StrategyHeader>           # 이름, 설명, 저장/실행 버튼
  ├─ <StepWizard>               # 단계별 입력
  │   ├─ <Step1_IndicatorSelector>
  │   ├─ <Step2_EntryBuilder>
  │   │   ├─ <LongConditions>
  │   │   │   └─ <ConditionRow>[]
  │   │   └─ <ShortConditions>
  │   │       └─ <ConditionRow>[]
  │   ├─ <Step3_StopLossSelector>
  │   └─ <Advanced>
  │       ├─ <ReverseSettings>
  │       └─ <HookSettings>
  └─ <JsonPreviewPanel>         # Read-only JSON
```

### 6.2 주요 컴포넌트 상세

#### 6.2.1 StrategyBuilderPage

```typescript
// app/strategies/builder/page.tsx

'use client';

import { useState } from 'react';
import { StrategyDraft, createEmptyDraft } from '@/lib/strategy-draft-utils';
import { StrategyHeader } from './components/StrategyHeader';
import { StepWizard } from './components/StepWizard';
import { JsonPreviewPanel } from './components/JsonPreviewPanel';
import { draftToStrategyJSON } from '@/lib/draft-to-json';
import { validateDraft } from '@/lib/draft-validation';

export default function StrategyBuilderPage() {
  // Draft State
  const [draft, setDraft] = useState<StrategyDraft>(createEmptyDraft());
  
  // Validation 결과
  const [errors, setErrors] = useState<ValidationError[]>([]);
  
  // 현재 Step
  const [currentStep, setCurrentStep] = useState<number>(1);
  
  // Draft 업데이트 핸들러
  const updateDraft = (updater: (draft: StrategyDraft) => StrategyDraft) => {
    const newDraft = updater(draft);
    setDraft(newDraft);
    
    // 실시간 Validation
    const validationResult = validateDraft(newDraft);
    setErrors(validationResult.errors);
  };
  
  // 저장 핸들러
  const handleSave = async () => {
    // Validation
    const validationResult = validateDraft(draft);
    if (!validationResult.isValid) {
      setErrors(validationResult.errors);
      return;
    }
    
    // Draft → JSON 변환
    const strategyJSON = draftToStrategyJSON(draft);
    
    // API 전송
    try {
      const response = await fetch('/api/strategies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(strategyJSON)
      });
      
      if (!response.ok) {
        throw new Error('전략 저장 실패');
      }
      
      // 성공 처리
      console.log('전략 저장 성공');
    } catch (error) {
      console.error(error);
    }
  };
  
  return (
    <div className="container mx-auto p-6">
      {/* 헤더 */}
      <StrategyHeader
        draft={draft}
        updateDraft={updateDraft}
        onSave={handleSave}
        errors={errors}
      />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* 좌측: Step Wizard */}
        <div className="lg:col-span-2">
          <StepWizard
            draft={draft}
            updateDraft={updateDraft}
            currentStep={currentStep}
            setCurrentStep={setCurrentStep}
            errors={errors}
          />
        </div>
        
        {/* 우측: JSON Preview */}
        <div className="lg:col-span-1">
          <JsonPreviewPanel draft={draft} />
        </div>
      </div>
    </div>
  );
}
```

#### 6.2.2 Step1_IndicatorSelector

```typescript
// app/strategies/builder/components/Step1_IndicatorSelector.tsx

'use client';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { IndicatorDraft } from '@/types/strategy-draft';

interface Step1Props {
  indicators: IndicatorDraft[];
  onAddIndicator: (indicator: IndicatorDraft) => void;
  onRemoveIndicator: (id: string) => void;
}

/**
 * Step 1: 지표 선택
 * 
 * 카드 기반 UI로 지표를 선택하고 추가
 */
export function Step1_IndicatorSelector({ 
  indicators, 
  onAddIndicator, 
  onRemoveIndicator 
}: Step1Props) {
  // 지표 카탈로그 (고정)
  const indicatorCatalog = [
    {
      type: 'ema',
      name: 'EMA (지수 이동평균)',
      category: 'Trend',
      defaultParams: { source: 'close', period: 20 }
    },
    {
      type: 'sma',
      name: 'SMA (단순 이동평균)',
      category: 'Trend',
      defaultParams: { source: 'close', period: 50 }
    },
    {
      type: 'rsi',
      name: 'RSI (상대강도지수)',
      category: 'Momentum',
      defaultParams: { source: 'close', period: 14 }
    },
    {
      type: 'atr',
      name: 'ATR (평균 진폭)',
      category: 'Volatility',
      defaultParams: { period: 14 }
    }
  ];
  
  // 지표 추가 핸들러
  const handleAddIndicator = (catalog: typeof indicatorCatalog[0]) => {
    // 자동 ID 생성 (타입_순번)
    const count = indicators.filter(i => i.type === catalog.type).length;
    const id = `${catalog.type}_${count + 1}`;
    
    const newIndicator: IndicatorDraft = {
      id,
      type: catalog.type as any,
      params: catalog.defaultParams
    };
    
    onAddIndicator(newIndicator);
  };
  
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Step 1: 지표 선택</h2>
        <p className="text-muted-foreground">
          전략에 사용할 지표를 선택하세요. 각 지표는 고유한 ID를 가집니다.
        </p>
      </div>
      
      {/* 지표 카탈로그 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {indicatorCatalog.map(catalog => (
          <Card key={catalog.type} className="p-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold">{catalog.name}</h3>
                <p className="text-sm text-muted-foreground">{catalog.category}</p>
              </div>
              <Button 
                size="sm" 
                onClick={() => handleAddIndicator(catalog)}
              >
                추가
              </Button>
            </div>
          </Card>
        ))}
      </div>
      
      {/* 추가된 지표 목록 */}
      {indicators.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold">추가된 지표 ({indicators.length})</h3>
          {indicators.map(indicator => (
            <Card key={indicator.id} className="p-3 flex justify-between items-center">
              <div>
                <span className="font-mono text-sm">{indicator.id}</span>
                <span className="mx-2">-</span>
                <span className="text-sm">{indicator.type.toUpperCase()}</span>
                <span className="mx-2 text-muted-foreground">|</span>
                <span className="text-xs text-muted-foreground">
                  {JSON.stringify(indicator.params)}
                </span>
              </div>
              <Button 
                variant="destructive" 
                size="sm"
                onClick={() => onRemoveIndicator(indicator.id)}
              >
                삭제
              </Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### 6.2.3 ConditionRow

```typescript
// app/strategies/builder/components/ConditionRow.tsx

'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ConditionDraft, IndicatorDraft } from '@/types/strategy-draft';
import { X } from 'lucide-react';

interface ConditionRowProps {
  condition: ConditionDraft;
  indicators: IndicatorDraft[];
  onChange: (updated: ConditionDraft) => void;
  onRemove: () => void;
}

/**
 * 조건 Row (문장형 UI)
 * 
 * 예: [ema_fast] [>] [ema_slow]
 */
export function ConditionRow({ 
  condition, 
  indicators, 
  onChange, 
  onRemove 
}: ConditionRowProps) {
  // 연산자 옵션
  const operators = [
    { value: '>', label: '>' },
    { value: '<', label: '<' },
    { value: '>=', label: '>=' },
    { value: '<=', label: '<=' },
    { value: 'cross_above', label: 'cross above (상향돌파)' },
    { value: 'cross_below', label: 'cross below (하향돌파)' }
  ];
  
  return (
    <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
      {/* 좌변 */}
      <Select
        value={condition.left.value.toString()}
        onValueChange={(value) => {
          // indicator 또는 number 판별
          const isNumber = !isNaN(Number(value));
          onChange({
            ...condition,
            left: {
              type: isNumber ? 'number' : 'indicator',
              value: isNumber ? Number(value) : value
            }
          });
        }}
      >
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="좌변 선택" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__number__">숫자 입력</SelectItem>
          {indicators.map(ind => (
            <SelectItem key={ind.id} value={ind.id}>
              {ind.id} ({ind.type})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {/* 좌변이 숫자인 경우 입력 필드 */}
      {condition.left.type === 'number' && (
        <Input
          type="number"
          value={condition.left.value}
          onChange={(e) => onChange({
            ...condition,
            left: { type: 'number', value: Number(e.target.value) }
          })}
          className="w-[100px]"
        />
      )}
      
      {/* 연산자 */}
      <Select
        value={condition.operator}
        onValueChange={(value) => onChange({ ...condition, operator: value as any })}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {operators.map(op => (
            <SelectItem key={op.value} value={op.value}>
              {op.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {/* 우변 */}
      <Select
        value={condition.right.value.toString()}
        onValueChange={(value) => {
          const isNumber = !isNaN(Number(value));
          onChange({
            ...condition,
            right: {
              type: isNumber ? 'number' : 'indicator',
              value: isNumber ? Number(value) : value
            }
          });
        }}
      >
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="우변 선택" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__number__">숫자 입력</SelectItem>
          {indicators.map(ind => (
            <SelectItem key={ind.id} value={ind.id}>
              {ind.id} ({ind.type})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {/* 우변이 숫자인 경우 */}
      {condition.right.type === 'number' && (
        <Input
          type="number"
          value={condition.right.value}
          onChange={(e) => onChange({
            ...condition,
            right: { type: 'number', value: Number(e.target.value) }
          })}
          className="w-[100px]"
        />
      )}
      
      {/* 삭제 버튼 */}
      <Button variant="ghost" size="icon" onClick={onRemove}>
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

#### 6.2.4 JsonPreviewPanel

```typescript
// app/strategies/builder/components/JsonPreviewPanel.tsx

'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StrategyDraft } from '@/types/strategy-draft';
import { draftToStrategyJSON } from '@/lib/draft-to-json';
import { Copy, Download } from 'lucide-react';

interface JsonPreviewPanelProps {
  draft: StrategyDraft;
}

/**
 * JSON Preview Panel (Read-only)
 * 
 * Draft State를 실시간으로 JSON으로 변환하여 표시
 */
export function JsonPreviewPanel({ draft }: JsonPreviewPanelProps) {
  // Draft → JSON 변환
  let jsonString = '';
  let hasError = false;
  
  try {
    const strategyJSON = draftToStrategyJSON(draft);
    jsonString = JSON.stringify(strategyJSON, null, 2);
  } catch (error) {
    hasError = true;
    jsonString = `// Validation 오류\n// ${(error as Error).message}`;
  }
  
  // 복사 핸들러
  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
  };
  
  // 다운로드 핸들러
  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${draft.name || 'strategy'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  return (
    <Card className="p-4 sticky top-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold">JSON Preview</h3>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={handleCopy} disabled={hasError}>
            <Copy className="h-4 w-4 mr-1" />
            복사
          </Button>
          <Button size="sm" variant="outline" onClick={handleDownload} disabled={hasError}>
            <Download className="h-4 w-4 mr-1" />
            다운로드
          </Button>
        </div>
      </div>
      
      <pre className="bg-muted p-4 rounded text-xs overflow-auto max-h-[600px]">
        <code className={hasError ? 'text-destructive' : ''}>
          {jsonString}
        </code>
      </pre>
    </Card>
  );
}
```

---

## 7. 단계별 구현 가이드

### Phase 1: 프로젝트 설정 (1일)

#### 1.1 Next.js 프로젝트 생성
```bash
# apps/web 디렉토리에서
pnpm create next-app@latest . --typescript --tailwind --app
```

#### 1.2 ShadCN 설치
```bash
pnpm dlx shadcn-ui@latest init
```

#### 1.3 필요한 컴포넌트 추가
```bash
pnpm dlx shadcn-ui@latest add button
pnpm dlx shadcn-ui@latest add card
pnpm dlx shadcn-ui@latest add input
pnpm dlx shadcn-ui@latest add select
pnpm dlx shadcn-ui@latest add tabs
pnpm dlx shadcn-ui@latest add alert
```

#### 1.4 폴더 구조 생성
```
apps/web/
├─ app/
│  └─ strategies/
│     └─ builder/
│        ├─ page.tsx
│        └─ components/
│           ├─ StrategyHeader.tsx
│           ├─ StepWizard.tsx
│           ├─ Step1_IndicatorSelector.tsx
│           ├─ Step2_EntryBuilder.tsx
│           ├─ Step3_StopLossSelector.tsx
│           ├─ ConditionRow.tsx
│           └─ JsonPreviewPanel.tsx
├─ lib/
│  ├─ strategy-draft-utils.ts
│  ├─ draft-validation.ts
│  └─ draft-to-json.ts
└─ types/
   └─ strategy-draft.ts
```

### Phase 2: Draft State 구현 (2일)

#### 2.1 타입 정의
- `types/strategy-draft.ts` 작성
- 모든 Draft 인터페이스 정의

#### 2.2 유틸 함수 작성
```typescript
// lib/strategy-draft-utils.ts

import { StrategyDraft, ConditionDraft } from '@/types/strategy-draft';
import { v4 as uuidv4 } from 'uuid';  // 임시 ID용

/**
 * 빈 Draft 생성
 */
export function createEmptyDraft(): StrategyDraft {
  return {
    name: '',
    description: '',
    indicators: [],
    entry: {
      long: { conditions: [] },
      short: { conditions: [] }
    },
    stopLoss: { type: 'fixed_percent', percent: 2 },
    reverse: { enabled: true, mode: 'use_entry_opposite' },
    hook: { enabled: false }
  };
}

/**
 * 빈 조건 생성
 */
export function createEmptyCondition(): ConditionDraft {
  return {
    tempId: uuidv4(),
    left: { type: 'indicator', value: '' },
    operator: '>',
    right: { type: 'indicator', value: '' }
  };
}
```

### Phase 3: Validation 구현 (2일)

#### 3.1 Validation 함수

```typescript
// lib/draft-validation.ts

import { StrategyDraft } from '@/types/strategy-draft';

export interface ValidationError {
  field: string;
  message: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

/**
 * Draft Validation
 * 
 * PRD/TRD 규칙을 모두 검증
 */
export function validateDraft(draft: StrategyDraft): ValidationResult {
  const errors: ValidationError[] = [];
  
  // 1. 이름 필수
  if (!draft.name.trim()) {
    errors.push({ field: 'name', message: '전략 이름은 필수입니다' });
  }
  
  // 2. Indicator ID 중복 체크
  const indicatorIds = draft.indicators.map(i => i.id);
  const uniqueIds = new Set(indicatorIds);
  if (indicatorIds.length !== uniqueIds.size) {
    errors.push({ 
      field: 'indicators', 
      message: '지표 ID가 중복되었습니다' 
    });
  }
  
  // 3. Entry 조건 최소 1개 (롱 또는 숏)
  const hasLongConditions = draft.entry.long.conditions.length > 0;
  const hasShortConditions = draft.entry.short.conditions.length > 0;
  
  if (!hasLongConditions && !hasShortConditions) {
    errors.push({ 
      field: 'entry', 
      message: '롱 또는 숏 진입 조건이 최소 1개 필요합니다' 
    });
  }
  
  // 4. 진입 조건 Validation
  const allConditions = [
    ...draft.entry.long.conditions,
    ...draft.entry.short.conditions
  ];
  
  for (const condition of allConditions) {
    // 좌변/우변이 비어있는지 체크
    if (!condition.left.value) {
      errors.push({ 
        field: 'entry', 
        message: '조건의 좌변이 비어있습니다' 
      });
    }
    if (!condition.right.value) {
      errors.push({ 
        field: 'entry', 
        message: '조건의 우변이 비어있습니다' 
      });
    }
    
    // cross 연산자 제약: 양쪽 모두 지표여야 함
    if (
      (condition.operator === 'cross_above' || condition.operator === 'cross_below') &&
      (condition.left.type !== 'indicator' || condition.right.type !== 'indicator')
    ) {
      errors.push({
        field: 'entry',
        message: 'cross 연산자는 양쪽 모두 지표여야 합니다'
      });
    }
  }
  
  // 5. Stop Loss 필수
  if (!draft.stopLoss) {
    errors.push({ 
      field: 'stopLoss', 
      message: '손절 방식은 필수입니다' 
    });
  }
  
  // ATR 기반 SL인 경우, ATR 지표 존재 확인
  if (draft.stopLoss.type === 'atr_based') {
    const atrExists = draft.indicators.some(
      i => i.id === draft.stopLoss.atr_indicator_id
    );
    if (!atrExists) {
      errors.push({
        field: 'stopLoss',
        message: 'ATR 지표를 먼저 추가해야 합니다'
      });
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}
```

### Phase 4: Draft → JSON 변환 (3일)

#### 4.1 변환 함수

```typescript
// lib/draft-to-json.ts

import { StrategyDraft, ConditionDraft } from '@/types/strategy-draft';

/**
 * Strategy JSON Schema v1.0 타입
 * 
 * 이 구조는 절대 변경 불가
 */
export interface StrategyJSON {
  schema_version: '1.0';
  meta: {
    name: string;
    description: string;
  };
  indicators: IndicatorJSON[];
  entry: EntryJSON;
  stop_loss: StopLossJSON;
  reverse: ReverseJSON;
  hook: HookJSON;
}

export interface IndicatorJSON {
  id: string;
  type: string;
  params: Record<string, any>;
}

export interface EntryJSON {
  long: { and: ConditionJSON[] };
  short: { and: ConditionJSON[] };
}

export interface ConditionJSON {
  left: { ref: string } | { value: number };
  op: string;
  right: { ref: string } | { value: number };
}

export type StopLossJSON =
  | { type: 'fixed_percent'; percent: number }
  | { type: 'atr_based'; atr_indicator_id: string; multiplier: number };

export type ReverseJSON =
  | { enabled: false }
  | { enabled: true; mode: 'use_entry_opposite' };

export interface HookJSON {
  enabled: boolean;
}

/**
 * Draft → Strategy JSON 변환
 * 
 * Validation은 이미 통과했다고 가정
 */
export function draftToStrategyJSON(draft: StrategyDraft): StrategyJSON {
  return {
    schema_version: '1.0',
    meta: {
      name: draft.name,
      description: draft.description
    },
    indicators: draft.indicators.map(convertIndicator),
    entry: {
      long: {
        and: draft.entry.long.conditions.map(convertCondition)
      },
      short: {
        and: draft.entry.short.conditions.map(convertCondition)
      }
    },
    stop_loss: convertStopLoss(draft.stopLoss),
    reverse: convertReverse(draft.reverse),
    hook: { enabled: draft.hook.enabled }
  };
}

/**
 * Indicator 변환
 */
function convertIndicator(indicator: any): IndicatorJSON {
  return {
    id: indicator.id,
    type: indicator.type,
    params: indicator.params
  };
}

/**
 * Condition 변환
 */
function convertCondition(condition: ConditionDraft): ConditionJSON {
  return {
    left: condition.left.type === 'indicator' 
      ? { ref: condition.left.value as string }
      : { value: condition.left.value as number },
    op: condition.operator,
    right: condition.right.type === 'indicator'
      ? { ref: condition.right.value as string }
      : { value: condition.right.value as number }
  };
}

/**
 * StopLoss 변환
 */
function convertStopLoss(stopLoss: any): StopLossJSON {
  if (stopLoss.type === 'fixed_percent') {
    return {
      type: 'fixed_percent',
      percent: stopLoss.percent
    };
  } else {
    return {
      type: 'atr_based',
      atr_indicator_id: stopLoss.atr_indicator_id,
      multiplier: stopLoss.multiplier
    };
  }
}

/**
 * Reverse 변환
 */
function convertReverse(reverse: any): ReverseJSON {
  if (!reverse.enabled) {
    return { enabled: false };
  }
  return {
    enabled: true,
    mode: 'use_entry_opposite'
  };
}
```

### Phase 5: 컴포넌트 구현 (5일)

각 컴포넌트를 순서대로 구현:
1. StrategyHeader (0.5일)
2. Step1_IndicatorSelector (1일)
3. Step2_EntryBuilder + ConditionRow (2일)
4. Step3_StopLossSelector (0.5일)
5. JsonPreviewPanel (0.5일)
6. StepWizard (통합, 0.5일)

### Phase 6: 테스트 및 디버깅 (2일)

---

## 8. Validation 규칙

### 8.1 필수 Validation

| 항목 | 규칙 | 에러 메시지 |
|------|------|------------|
| 전략 이름 | 필수, 공백 불가 | "전략 이름은 필수입니다" |
| Indicator ID | 중복 불가 | "지표 ID '{id}'가 중복되었습니다" |
| Entry 조건 | 롱 또는 숏 최소 1개 | "롱 또는 숏 진입 조건이 최소 1개 필요합니다" |
| Condition 좌변 | 필수 | "조건의 좌변이 비어있습니다" |
| Condition 우변 | 필수 | "조건의 우변이 비어있습니다" |
| cross 연산자 | 양쪽 모두 지표 | "cross 연산자는 양쪽 모두 지표여야 합니다" |
| Stop Loss | 필수 | "손절 방식은 필수입니다" |
| ATR 기반 SL | ATR 지표 존재 확인 | "ATR 지표를 먼저 추가해야 합니다" |

### 8.2 실시간 Validation

```typescript
// Draft 업데이트 시마다 Validation 실행
const updateDraft = (updater: (draft: StrategyDraft) => StrategyDraft) => {
  const newDraft = updater(draft);
  setDraft(newDraft);
  
  // 실시간 Validation
  const validationResult = validateDraft(newDraft);
  setErrors(validationResult.errors);
};
```

### 8.3 에러 표시

```typescript
// 에러가 있는 경우 저장 버튼 비활성화
<Button 
  onClick={handleSave}
  disabled={errors.length > 0}
>
  저장
</Button>

// 에러 목록 표시
{errors.length > 0 && (
  <Alert variant="destructive">
    <AlertTitle>Validation 오류</AlertTitle>
    <AlertDescription>
      <ul className="list-disc pl-5">
        {errors.map((err, idx) => (
          <li key={idx}>{err.message}</li>
        ))}
      </ul>
    </AlertDescription>
  </Alert>
)}
```

---

## 9. Draft → JSON 변환 로직

### 9.1 변환 순서

```
1. Meta 정보 변환
   - name, description

2. Indicators 변환
   - Draft indicators → JSON indicators
   - 순서 유지

3. Entry 조건 변환
   - long.conditions → entry.long.and
   - short.conditions → entry.short.and
   - ConditionDraft → ConditionJSON

4. Stop Loss 변환
   - StopLossDraft → StopLossJSON

5. Reverse 변환
   - ReverseDraft → ReverseJSON

6. Hook 변환
   - HookDraft → HookJSON
```

### 9.2 변환 예시

**Draft State**:
```json
{
  "name": "Simple EMA Cross",
  "indicators": [
    { "id": "ema_fast", "type": "ema", "params": { "source": "close", "period": 12 } },
    { "id": "ema_slow", "type": "ema", "params": { "source": "close", "period": 26 } }
  ],
  "entry": {
    "long": {
      "conditions": [
        {
          "left": { "type": "indicator", "value": "ema_fast" },
          "operator": "cross_above",
          "right": { "type": "indicator", "value": "ema_slow" }
        }
      ]
    }
  },
  "stopLoss": { "type": "fixed_percent", "percent": 2 }
}
```

**Strategy JSON**:
```json
{
  "schema_version": "1.0",
  "meta": {
    "name": "Simple EMA Cross",
    "description": ""
  },
  "indicators": [
    { "id": "ema_fast", "type": "ema", "params": { "source": "close", "period": 12 } },
    { "id": "ema_slow", "type": "ema", "params": { "source": "close", "period": 26 } }
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
      "and": []
    }
  },
  "stop_loss": {
    "type": "fixed_percent",
    "percent": 2
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

---

## 10. Canonicalization

### 10.1 목적
동일한 Draft State → 동일한 strategy_hash 보장

### 10.2 Canonicalization 규칙

```typescript
// lib/canonicalization.ts

/**
 * Strategy JSON Canonicalization
 * 
 * 1. meta 제외
 * 2. key 알파벳 정렬
 * 3. whitespace 제거
 * 4. 일관된 직렬화
 */
export function canonicalizeStrategyJSON(strategyJSON: StrategyJSON): string {
  // meta 제외한 복사본 생성
  const { meta, ...canonical } = strategyJSON;
  
  // 재귀적으로 key 정렬
  const sorted = sortKeys(canonical);
  
  // 최소화된 JSON 문자열
  return JSON.stringify(sorted);
}

/**
 * 객체의 key를 재귀적으로 정렬
 */
function sortKeys(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(sortKeys);
  }
  
  if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj)
      .sort()
      .reduce((result, key) => {
        result[key] = sortKeys(obj[key]);
        return result;
      }, {} as any);
  }
  
  return obj;
}

/**
 * Strategy Hash 계산
 */
export async function calculateStrategyHash(strategyJSON: StrategyJSON): Promise<string> {
  const canonical = canonicalizeStrategyJSON(strategyJSON);
  
  // SHA-256 해시
  const encoder = new TextEncoder();
  const data = encoder.encode(canonical);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  
  // Hex 문자열로 변환
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  return hashHex;
}
```

### 10.3 사용 예시

```typescript
// 저장 시 hash 계산
const strategyJSON = draftToStrategyJSON(draft);
const strategyHash = await calculateStrategyHash(strategyJSON);

// API 전송
await fetch('/api/strategies', {
  method: 'POST',
  body: JSON.stringify({
    ...strategyJSON,
    strategy_hash: strategyHash
  })
});
```

---

## 11. 테스트 전략

### 11.1 단위 테스트

```typescript
// __tests__/draft-validation.test.ts

import { validateDraft } from '@/lib/draft-validation';
import { createEmptyDraft } from '@/lib/strategy-draft-utils';

describe('Draft Validation', () => {
  test('빈 Draft는 Validation 실패', () => {
    const draft = createEmptyDraft();
    const result = validateDraft(draft);
    
    expect(result.isValid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });
  
  test('Indicator ID 중복 감지', () => {
    const draft = createEmptyDraft();
    draft.indicators = [
      { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
      { id: 'ema_1', type: 'ema', params: { source: 'close', period: 26 } }
    ];
    
    const result = validateDraft(draft);
    
    expect(result.isValid).toBe(false);
    expect(result.errors.some(e => e.field === 'indicators')).toBe(true);
  });
  
  test('cross 연산자는 양쪽 모두 지표', () => {
    const draft = createEmptyDraft();
    draft.entry.long.conditions = [
      {
        tempId: '1',
        left: { type: 'number', value: 50 },
        operator: 'cross_above',
        right: { type: 'indicator', value: 'ema_1' }
      }
    ];
    
    const result = validateDraft(draft);
    
    expect(result.isValid).toBe(false);
    expect(result.errors.some(e => e.message.includes('cross'))).toBe(true);
  });
});
```

### 11.2 통합 테스트

```typescript
// __tests__/draft-to-json.test.ts

import { draftToStrategyJSON } from '@/lib/draft-to-json';
import { StrategyDraft } from '@/types/strategy-draft';

describe('Draft to JSON Conversion', () => {
  test('기본 Draft → JSON 변환', () => {
    const draft: StrategyDraft = {
      name: 'Test Strategy',
      description: 'Test',
      indicators: [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ],
      entry: {
        long: {
          conditions: [
            {
              tempId: '1',
              left: { type: 'indicator', value: 'ema_1' },
              operator: '>',
              right: { type: 'number', value: 100 }
            }
          ]
        },
        short: { conditions: [] }
      },
      stopLoss: { type: 'fixed_percent', percent: 2 },
      reverse: { enabled: true, mode: 'use_entry_opposite' },
      hook: { enabled: false }
    };
    
    const json = draftToStrategyJSON(draft);
    
    expect(json.schema_version).toBe('1.0');
    expect(json.meta.name).toBe('Test Strategy');
    expect(json.indicators.length).toBe(1);
    expect(json.entry.long.and.length).toBe(1);
  });
  
  test('동일 Draft → 동일 JSON', () => {
    const draft1 = { /* ... */ };
    const draft2 = { /* ... */ };  // draft1과 동일
    
    const json1 = draftToStrategyJSON(draft1);
    const json2 = draftToStrategyJSON(draft2);
    
    expect(JSON.stringify(json1)).toBe(JSON.stringify(json2));
  });
});
```

### 11.3 E2E 테스트 (Playwright)

```typescript
// e2e/strategy-builder.spec.ts

import { test, expect } from '@playwright/test';

test('전략 빌더 플로우', async ({ page }) => {
  // 페이지 방문
  await page.goto('/strategies/builder');
  
  // 전략 이름 입력
  await page.fill('input[name="name"]', 'Test Strategy');
  
  // Step 1: EMA 지표 추가
  await page.click('text=EMA 추가');
  
  // Step 2: 진입 조건 추가
  await page.click('text=조건 추가');
  
  // JSON Preview 확인
  const jsonPreview = page.locator('pre code');
  await expect(jsonPreview).toContainText('"schema_version": "1.0"');
  
  // 저장 버튼 클릭
  await page.click('text=저장');
  
  // 성공 메시지 확인
  await expect(page.locator('text=저장 성공')).toBeVisible();
});
```

---

## 12. 구현 체크리스트

### Phase 1: 프로젝트 설정
- [ ] Next.js 프로젝트 생성
- [ ] ShadCN 설치 및 설정
- [ ] 필요한 컴포넌트 추가
- [ ] 폴더 구조 생성

### Phase 2: Draft State
- [ ] Draft State 타입 정의 (`types/strategy-draft.ts`)
- [ ] 유틸 함수 작성 (`lib/strategy-draft-utils.ts`)
- [ ] 초기 Draft 생성 함수

### Phase 3: Validation
- [ ] Validation 함수 구현 (`lib/draft-validation.ts`)
- [ ] 모든 PRD/TRD 규칙 검증 로직
- [ ] 실시간 Validation 적용
- [ ] 에러 메시지 정의

### Phase 4: Draft → JSON 변환
- [ ] Strategy JSON 타입 정의
- [ ] 변환 함수 구현 (`lib/draft-to-json.ts`)
- [ ] Canonicalization 함수
- [ ] strategy_hash 계산 함수

### Phase 5: 컴포넌트 구현
- [ ] StrategyBuilderPage
- [ ] StrategyHeader
- [ ] Step1_IndicatorSelector
- [ ] Step2_EntryBuilder
- [ ] ConditionRow
- [ ] Step3_StopLossSelector
- [ ] JsonPreviewPanel
- [ ] StepWizard

### Phase 6: 고급 기능
- [ ] Reverse 설정 컴포넌트
- [ ] Hook 설정 컴포넌트 (기본 OFF)
- [ ] 지표 파라미터 수정 UI

### Phase 7: API 연동
- [ ] 저장 API 연동 (`POST /api/strategies`)
- [ ] 전략 목록 조회
- [ ] 전략 수정 (기존 전략 불러오기)

### Phase 8: 테스트
- [ ] 단위 테스트 (Validation)
- [ ] 단위 테스트 (Draft → JSON)
- [ ] 통합 테스트
- [ ] E2E 테스트
- [ ] 결정성 테스트 (동일 Draft → 동일 hash)

### Phase 9: 문서화
- [ ] 컴포넌트 docstring
- [ ] README 작성
- [ ] 사용자 가이드

### Phase 10: 최종 검증
- [ ] UI로 만든 JSON이 수동 작성 JSON과 100% 호환
- [ ] 동일 Draft → 동일 strategy_hash 확인
- [ ] PRD/TRD 규칙 모두 준수 확인
- [ ] Validation 규칙 모두 동작 확인

---

## 부록 A: 주요 파일 목록

```
apps/web/
├─ app/strategies/builder/
│  ├─ page.tsx                         # 메인 페이지
│  └─ components/
│     ├─ StrategyHeader.tsx            # 헤더 (이름, 저장 버튼)
│     ├─ StepWizard.tsx                # Step 관리
│     ├─ Step1_IndicatorSelector.tsx   # 지표 선택
│     ├─ Step2_EntryBuilder.tsx        # 진입 조건
│     ├─ Step3_StopLossSelector.tsx    # 손절 방식
│     ├─ ConditionRow.tsx              # 조건 Row
│     └─ JsonPreviewPanel.tsx          # JSON 미리보기
├─ lib/
│  ├─ strategy-draft-utils.ts          # Draft 유틸
│  ├─ draft-validation.ts              # Validation
│  ├─ draft-to-json.ts                 # Draft → JSON
│  └─ canonicalization.ts              # Canonicalization
├─ types/
│  └─ strategy-draft.ts                # Draft 타입
└─ __tests__/
   ├─ draft-validation.test.ts
   └─ draft-to-json.test.ts
```

---

## 부록 B: 금지 패턴

### ❌ 금지 패턴 1: JSON 구조 단순화
```typescript
// 나쁜 예: JSON 구조를 단순화
export interface SimplifiedEntryJSON {
  long: string[];  // 문자열 배열로 단순화
  short: string[];
}

// 좋은 예: Schema v1.0 준수
export interface EntryJSON {
  long: { and: ConditionJSON[] };
  short: { and: ConditionJSON[] };
}
```

### ❌ 금지 패턴 2: 자동 보정
```typescript
// 나쁜 예: Validation 실패 시 자동 수정
if (condition.left.value === '') {
  condition.left.value = 'default_indicator';  // 자동 보정
}

// 좋은 예: Validation 실패 시 에러 반환
if (condition.left.value === '') {
  errors.push({ field: 'entry', message: '좌변이 비어있습니다' });
}
```

### ❌ 금지 패턴 3: 비결정적 요소
```typescript
// 나쁜 예: timestamp 사용
const strategyJSON = {
  ...draft,
  created_at: Date.now()  // 비결정적
};

// 좋은 예: 결정적 요소만 사용
const strategyJSON = draftToStrategyJSON(draft);
```

---

## 마치며

이 가이드는 AlgoForge 전략 빌더 UI 구현을 위한 완벽한 로드맵입니다.

### 핵심 원칙 재확인
1. **Strategy JSON Schema v1.0은 절대 변경 금지**
2. **Draft State는 UI 전용, JSON은 Draft에서만 생성**
3. **Validation 실패 시 JSON 생성 금지**
4. **동일 Draft → 동일 strategy_hash 보장**
5. **PRD/TRD 규칙 절대 준수**

### 성공 기준
```
✅ UI로 만든 전략 JSON이 기존 수동 작성 JSON과 100% 호환
✅ 동일 Draft → 동일 strategy_hash 생성 가능
✅ PRD/TRD의 모든 규칙을 UI에서 강제
✅ JSON을 모르는 사용자도 전략 작성 가능
```

**Good Luck!** 🚀

