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
import type { Indicator } from '@/lib/types';

interface ConditionRowProps {
  condition: ConditionDraft;
  indicators: IndicatorDraft[];
  availableIndicators: Indicator[];
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

// OHLCV 옵션
const OHLCV_OPTIONS = [
  { value: 'open', label: 'Open (시가)' },
  { value: 'high', label: 'High (고가)' },
  { value: 'low', label: 'Low (저가)' },
  { value: 'close', label: 'Close (종가)' },
  { value: 'volume', label: 'Volume (거래량)' }
] as const;

/**
 * 조건 Row
 * 
 * 좌변 - 연산자 - 우변 형태로 조건 입력
 */
export function ConditionRow({ 
  condition, 
  indicators,
  availableIndicators,
  onChange, 
  onRemove 
}: ConditionRowProps) {
  
  // OHLCV 값인지 확인
  const isOHLCV = (value: string) => {
    return ['open', 'high', 'low', 'close', 'volume'].includes(value);
  };
  
  // 좌변 선택 핸들러
  const handleLeftChange = (value: string) => {
    if (value === '__number__') {
      onChange({
        ...condition,
        left: { type: 'number', value: 0 }
      });
    } else if (isOHLCV(value)) {
      onChange({
        ...condition,
        left: { type: 'price', value }
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
    } else if (isOHLCV(value)) {
      onChange({
        ...condition,
        right: { type: 'price', value }
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
          
          {/* OHLCV 옵션 */}
          <optgroup label="━━━ OHLCV ━━━">
            {OHLCV_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </optgroup>
          
          {/* 지표 옵션 */}
          <optgroup label="━━━ 지표 ━━━">
            {indicators.map(ind => {
              // 해당 지표의 메타 정보 찾기
              const indicatorInfo = availableIndicators?.find(i => i.type === ind.type);
              const outputFields = indicatorInfo?.output_fields || ['main'];
              
              // 디버깅 로그 (좌변) - 강화
              console.log(`[ConditionRow-좌변] ${ind.id} (${ind.type})`);
              console.log('  → indicatorInfo:', indicatorInfo ? 'FOUND' : 'NOT FOUND');
              console.log('  → outputFields:', outputFields, `(${outputFields.length}개)`);
              console.log('  → availableIndicators 개수:', availableIndicators?.length || 0);
              
              // 모든 지표를 "지표.값" 형태로 표시
              return outputFields.map(field => {
                // 표시명 생성 (항상 점 사용)
                let displayLabel: string;
                let storageValue: string;
                
                if (outputFields.length === 1 && field === 'main') {
                  // 단일 출력 (내장 지표): 지표 타입명으로 표시
                  displayLabel = `${ind.id}.${ind.type}`;
                  // 저장값은 점 없이 (백엔드 컬럼명과 일치)
                  storageValue = ind.id;
                } else {
                  // 다중 출력 또는 추가 필드: 필드명 사용
                  displayLabel = `${ind.id}.${field}`;
                  // 저장값은 점(.)으로 구분 (백엔드에서 _로 변환)
                  storageValue = `${ind.id}.${field}`;
                }
                
                console.log(`    ✓ 옵션 생성: ${displayLabel} (value: ${storageValue})`);
                
                return (
                  <option key={storageValue} value={storageValue}>
                    {displayLabel}
                  </option>
                );
              });
            })}
          </optgroup>
          
          {/* 숫자 입력 */}
          <optgroup label="━━━ 기타 ━━━">
            <option value="__number__">숫자 입력</option>
          </optgroup>
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
          
          {/* OHLCV 옵션 */}
          <optgroup label="━━━ OHLCV ━━━">
            {OHLCV_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </optgroup>
          
          {/* 지표 옵션 */}
          <optgroup label="━━━ 지표 ━━━">
            {indicators.map(ind => {
              // 해당 지표의 메타 정보 찾기
              const indicatorInfo = availableIndicators?.find(i => i.type === ind.type);
              const outputFields = indicatorInfo?.output_fields || ['main'];
              
              // 디버깅 로그 (우변) - 강화
              console.log(`[ConditionRow-우변] ${ind.id} (${ind.type})`);
              console.log('  → indicatorInfo:', indicatorInfo ? 'FOUND' : 'NOT FOUND');
              console.log('  → outputFields:', outputFields, `(${outputFields.length}개)`);
              console.log('  → availableIndicators 개수:', availableIndicators?.length || 0);
              
              // 모든 지표를 "지표.값" 형태로 표시
              return outputFields.map(field => {
                // 표시명 생성 (항상 점 사용)
                let displayLabel: string;
                let storageValue: string;
                
                if (outputFields.length === 1 && field === 'main') {
                  // 단일 출력 (내장 지표): 지표 타입명으로 표시
                  displayLabel = `${ind.id}.${ind.type}`;
                  // 저장값은 점 없이 (백엔드 컬럼명과 일치)
                  storageValue = ind.id;
                } else {
                  // 다중 출력 또는 추가 필드: 필드명 사용
                  displayLabel = `${ind.id}.${field}`;
                  // 저장값은 점(.)으로 구분 (백엔드에서 _로 변환)
                  storageValue = `${ind.id}.${field}`;
                }
                
                console.log(`    ✓ 옵션 생성: ${displayLabel} (value: ${storageValue})`);
                
                return (
                  <option key={storageValue} value={storageValue}>
                    {displayLabel}
                  </option>
                );
              });
            })}
          </optgroup>
          
          {/* 숫자 입력 */}
          <optgroup label="━━━ 기타 ━━━">
            <option value="__number__">숫자 입력</option>
          </optgroup>
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

