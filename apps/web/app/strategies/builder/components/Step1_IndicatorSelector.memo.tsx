/**
 * Step 1: 지표 선택 컴포넌트 (메모이제이션 버전)
 * 
 * React.memo를 사용하여 불필요한 리렌더링 방지
 */

'use client';

import React, { useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Trash2, TrendingUp, Activity, BarChart3 } from 'lucide-react';
import { IndicatorIdEditor } from './IndicatorIdEditor';
import type { IndicatorDraft } from '@/types/strategy-draft';

interface Step1Props {
  indicators: IndicatorDraft[];
  onAddIndicator: (indicator: IndicatorDraft) => void;
  onRemoveIndicator: (id: string) => void;
  onUpdateIndicator: (id: string, updatedIndicator: IndicatorDraft) => void;
}

// 지표 카탈로그 (고정) - 컴포넌트 외부로 이동하여 재생성 방지
const INDICATOR_CATALOG = [
  {
    type: 'ema',
    name: 'EMA (지수 이동평균)',
    category: 'Trend',
    icon: TrendingUp,
    defaultParams: { source: 'close', period: 20 }
  },
  {
    type: 'sma',
    name: 'SMA (단순 이동평균)',
    category: 'Trend',
    icon: TrendingUp,
    defaultParams: { source: 'close', period: 50 }
  },
  {
    type: 'rsi',
    name: 'RSI (상대강도지수)',
    category: 'Momentum',
    icon: Activity,
    defaultParams: { source: 'close', period: 14 }
  },
  {
    type: 'atr',
    name: 'ATR (평균 진폭)',
    category: 'Volatility',
    icon: BarChart3,
    defaultParams: { period: 14 }
  },
  {
    type: 'adx',
    name: 'ADX (Average Directional Index)',
    category: 'Trend',
    icon: TrendingUp,
    defaultParams: { period: 14 }
  }
] as const;

/**
 * 개별 지표 카드 컴포넌트 (메모이제이션)
 */
const IndicatorCard = React.memo(function IndicatorCard({
  indicator,
  allIndicators,
  onRemove,
  onUpdateId,
  onParamUpdate
}: {
  indicator: IndicatorDraft;
  allIndicators: IndicatorDraft[];
  onRemove: () => void;
  onUpdateId: (newId: string) => void;
  onParamUpdate: (paramKey: string, value: any) => void;
}) {
  // 다른 지표들의 ID 목록
  const existingIds = allIndicators
    .filter(i => i.id !== indicator.id)
    .map(i => i.id);
  
  return (
    <Card className="p-4">
      <div className="space-y-3">
        {/* ID 편집기 */}
        <div className="flex items-center justify-between">
          <IndicatorIdEditor
            currentId={indicator.id}
            existingIds={existingIds}
            onUpdate={onUpdateId}
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={onRemove}
            title="삭제"
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
        
        {/* 지표 타입 */}
        <div className="text-sm text-muted-foreground">
          {indicator.type.toUpperCase()}
        </div>
        
        {/* 파라미터 편집 */}
        <div className="space-y-2">
          {Object.entries(indicator.params).map(([key, value]) => (
            <div key={key} className="space-y-1">
              <Label htmlFor={`${indicator.id}-${key}`} className="text-xs">
                {key}
              </Label>
              <Input
                id={`${indicator.id}-${key}`}
                type={typeof value === 'number' ? 'number' : 'text'}
                value={value}
                onChange={(e) => {
                  const newValue = typeof value === 'number' 
                    ? Number(e.target.value) 
                    : e.target.value;
                  onParamUpdate(key, newValue);
                }}
                className="h-8 text-sm"
              />
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
});

/**
 * Step 1: 지표 선택 (메모이제이션)
 */
export const Step1_IndicatorSelectorMemo = React.memo(function Step1_IndicatorSelector({ 
  indicators, 
  onAddIndicator, 
  onRemoveIndicator,
  onUpdateIndicator
}: Step1Props) {
  
  // 지표 추가 핸들러 (useCallback으로 메모이제이션)
  const handleAddIndicator = useCallback((catalog: typeof INDICATOR_CATALOG[number]) => {
    // 자동 ID 생성 (타입_순번)
    const count = indicators.filter(i => i.type === catalog.type).length;
    const id = `${catalog.type}_${count + 1}`;
    
    const newIndicator: IndicatorDraft = {
      id,
      type: catalog.type as any,
      params: { ...catalog.defaultParams }
    };
    
    onAddIndicator(newIndicator);
  }, [indicators, onAddIndicator]);
  
  // 지표 파라미터 업데이트 핸들러 생성 (useMemo)
  const indicatorHandlers = useMemo(() => {
    return indicators.map(indicator => ({
      id: indicator.id,
      onRemove: () => onRemoveIndicator(indicator.id),
      onUpdateId: (newId: string) => {
        const updated: IndicatorDraft = {
          ...indicator,
          id: newId
        };
        onUpdateIndicator(indicator.id, updated);
      },
      onParamUpdate: (paramKey: string, value: any) => {
        const updated: IndicatorDraft = {
          ...indicator,
          params: {
            ...indicator.params,
            [paramKey]: value
          }
        };
        onUpdateIndicator(indicator.id, updated);
      }
    }));
  }, [indicators, onRemoveIndicator, onUpdateIndicator]);
  
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
        {INDICATOR_CATALOG.map(catalog => {
          const Icon = catalog.icon;
          return (
            <Card key={catalog.type} className="p-4 hover:bg-accent/50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{catalog.name}</h3>
                    <p className="text-sm text-muted-foreground">{catalog.category}</p>
                  </div>
                </div>
                <Button 
                  size="sm" 
                  onClick={() => handleAddIndicator(catalog)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
      
      {/* 추가된 지표 목록 */}
      {indicators.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold">추가된 지표 ({indicators.length})</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {indicators.map((indicator, index) => {
              const handlers = indicatorHandlers[index];
              return (
                <IndicatorCard
                  key={indicator.id}
                  indicator={indicator}
                  allIndicators={indicators}
                  onRemove={handlers.onRemove}
                  onUpdateId={handlers.onUpdateId}
                  onParamUpdate={handlers.onParamUpdate}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
});

