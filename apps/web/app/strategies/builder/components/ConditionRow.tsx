/**
 * 조건 Row 컴포넌트
 * 
 * 문장형 UI로 조건을 입력받음
 * 예: [ema_fast] [>] [ema_slow]
 */

'use client';

import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import type { ConditionDraft, IndicatorDraft } from '@/types/strategy-draft';

interface ConditionRowProps {
  condition: ConditionDraft;
  indicators: IndicatorDraft[];
  onChange: (updated: ConditionDraft) => void;
  onRemove: () => void;
}

// 연산자 옵션
const OPERATORS = [
  { value: '>', label: '>' },
  { value: '<', label: '<' },
  { value: '>=', label: '>=' },
  { value: '<=', label: '<=' },
  { value: 'cross_above', label: 'cross above (상향돌파)' },
  { value: 'cross_below', label: 'cross below (하향돌파)' }
] as const;

/**
 * 조건 Row
 * 
 * 좌변 - 연산자 - 우변 형태로 조건 입력
 */
export function ConditionRow({ 
  condition, 
  indicators, 
  onChange, 
  onRemove 
}: ConditionRowProps) {
  
  // 좌변 선택 핸들러
  const handleLeftChange = (value: string) => {
    if (value === '__number__') {
      onChange({
        ...condition,
        left: { type: 'number', value: 0 }
      });
    } else {
      onChange({
        ...condition,
        left: { type: 'indicator', value }
      });
    }
  };
  
  // 우변 선택 핸들러
  const handleRightChange = (value: string) => {
    if (value === '__number__') {
      onChange({
        ...condition,
        right: { type: 'number', value: 0 }
      });
    } else {
      onChange({
        ...condition,
        right: { type: 'indicator', value }
      });
    }
  };
  
  return (
    <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg border">
      {/* 좌변 선택 */}
      <div className="flex-1 space-y-1">
        <select
          value={condition.left.type === 'number' ? '__number__' : condition.left.value}
          onChange={(e) => handleLeftChange(e.target.value)}
          className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm"
        >
          <option value="">좌변 선택</option>
          <option value="__number__">숫자 입력</option>
          {indicators.map(ind => (
            <option key={ind.id} value={ind.id}>
              {ind.id} ({ind.type.toUpperCase()})
            </option>
          ))}
        </select>
        
        {/* 좌변이 숫자인 경우 입력 필드 */}
        {condition.left.type === 'number' && (
          <Input
            type="number"
            value={condition.left.value}
            onChange={(e) => onChange({
              ...condition,
              left: { type: 'number', value: Number(e.target.value) }
            })}
            placeholder="숫자 입력"
            className="h-8"
            step="any"
          />
        )}
      </div>
      
      {/* 연산자 선택 */}
      <div className="w-[180px]">
        <select
          value={condition.operator}
          onChange={(e) => onChange({ 
            ...condition, 
            operator: e.target.value as any 
          })}
          className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm"
        >
          {OPERATORS.map(op => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </select>
      </div>
      
      {/* 우변 선택 */}
      <div className="flex-1 space-y-1">
        <select
          value={condition.right.type === 'number' ? '__number__' : condition.right.value}
          onChange={(e) => handleRightChange(e.target.value)}
          className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm"
        >
          <option value="">우변 선택</option>
          <option value="__number__">숫자 입력</option>
          {indicators.map(ind => (
            <option key={ind.id} value={ind.id}>
              {ind.id} ({ind.type.toUpperCase()})
            </option>
          ))}
        </select>
        
        {/* 우변이 숫자인 경우 입력 필드 */}
        {condition.right.type === 'number' && (
          <Input
            type="number"
            value={condition.right.value}
            onChange={(e) => onChange({
              ...condition,
              right: { type: 'number', value: Number(e.target.value) }
            })}
            placeholder="숫자 입력"
            className="h-8"
            step="any"
          />
        )}
      </div>
      
      {/* 삭제 버튼 */}
      <Button 
        variant="ghost" 
        size="icon" 
        onClick={onRemove}
        className="h-9 w-9"
      >
        <X className="h-4 w-4 text-muted-foreground hover:text-destructive" />
      </Button>
    </div>
  );
}

