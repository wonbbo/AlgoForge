/**
 * Step 1: 지표 선택 컴포넌트
 * 
 * 카드 기반 UI로 지표를 선택하고 추가
 */

'use client';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Trash2, TrendingUp, Activity, BarChart3 } from 'lucide-react';
import type { IndicatorDraft } from '@/types/strategy-draft';

interface Step1Props {
  indicators: IndicatorDraft[];
  onAddIndicator: (indicator: IndicatorDraft) => void;
  onRemoveIndicator: (id: string) => void;
  onUpdateIndicator: (id: string, updatedIndicator: IndicatorDraft) => void;
}

// 지표 카탈로그 (고정)
const INDICATOR_CATALOG = [
  {
    type: 'ema',
    name: 'EMA (지수 이동평균)',
    category: 'Trend',
    icon: TrendingUp,
    description: '최근 가격에 더 큰 가중치를 부여하는 이동평균',
    defaultParams: { source: 'close', period: 20 },
    paramConfig: [
      { key: 'source', label: 'Source', type: 'select', options: ['close', 'open', 'high', 'low'] },
      { key: 'period', label: 'Period', type: 'number', min: 1, max: 500 }
    ]
  },
  {
    type: 'sma',
    name: 'SMA (단순 이동평균)',
    category: 'Trend',
    icon: TrendingUp,
    description: '일정 기간의 평균 가격',
    defaultParams: { source: 'close', period: 50 },
    paramConfig: [
      { key: 'source', label: 'Source', type: 'select', options: ['close', 'open', 'high', 'low'] },
      { key: 'period', label: 'Period', type: 'number', min: 1, max: 500 }
    ]
  },
  {
    type: 'rsi',
    name: 'RSI (상대강도지수)',
    category: 'Momentum',
    icon: Activity,
    description: '과매수/과매도 상태를 나타내는 모멘텀 지표 (0-100)',
    defaultParams: { source: 'close', period: 14 },
    paramConfig: [
      { key: 'source', label: 'Source', type: 'select', options: ['close'] },
      { key: 'period', label: 'Period', type: 'number', min: 1, max: 100 }
    ]
  },
  {
    type: 'atr',
    name: 'ATR (평균 진폭)',
    category: 'Volatility',
    icon: BarChart3,
    description: '가격 변동성을 측정하는 지표',
    defaultParams: { period: 14 },
    paramConfig: [
      { key: 'period', label: 'Period', type: 'number', min: 1, max: 100 }
    ]
  }
] as const;

/**
 * Step 1: 지표 선택
 * 
 * 카드 기반 UI로 지표를 선택하고 추가
 */
export function Step1_IndicatorSelector({ 
  indicators, 
  onAddIndicator, 
  onRemoveIndicator,
  onUpdateIndicator
}: Step1Props) {
  
  // 지표 추가 핸들러
  const handleAddIndicator = (catalog: typeof INDICATOR_CATALOG[number]) => {
    // 자동 ID 생성 (타입_순번)
    const count = indicators.filter(i => i.type === catalog.type).length;
    const id = `${catalog.type}_${count + 1}`;
    
    const newIndicator: IndicatorDraft = {
      id,
      type: catalog.type as any,
      params: { ...catalog.defaultParams }
    };
    
    onAddIndicator(newIndicator);
  };
  
  // 지표 파라미터 업데이트
  const handleParamUpdate = (id: string, paramKey: string, value: any) => {
    const indicator = indicators.find(i => i.id === id);
    if (!indicator) return;
    
    const updated: IndicatorDraft = {
      ...indicator,
      params: {
        ...indicator.params,
        [paramKey]: value
      }
    };
    
    onUpdateIndicator(id, updated);
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
        {INDICATOR_CATALOG.map(catalog => {
          const Icon = catalog.icon;
          return (
            <Card key={catalog.type} className="p-4 hover:border-primary transition-colors">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold">{catalog.name}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-1">
                    {catalog.description}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    카테고리: {catalog.category}
                  </p>
                </div>
                <Button 
                  size="sm" 
                  onClick={() => handleAddIndicator(catalog)}
                  className="ml-2"
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
          <h3 className="font-semibold text-lg">추가된 지표 ({indicators.length})</h3>
          <div className="space-y-3">
            {indicators.map(indicator => {
              const catalog = INDICATOR_CATALOG.find(c => c.type === indicator.type);
              if (!catalog) return null;
              
              return (
                <Card key={indicator.id} className="p-4">
                  <div className="space-y-3">
                    {/* 지표 헤더 */}
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-semibold text-primary">
                            {indicator.id}
                          </span>
                          <span className="text-sm text-muted-foreground">-</span>
                          <span className="text-sm font-medium">
                            {catalog.name}
                          </span>
                        </div>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => onRemoveIndicator(indicator.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                    
                    {/* 파라미터 설정 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {catalog.paramConfig.map(config => (
                        <div key={config.key} className="space-y-1">
                          <Label className="text-xs">{config.label}</Label>
                          {config.type === 'number' ? (
                            <Input
                              type="number"
                              min={config.min}
                              max={config.max}
                              value={indicator.params[config.key]}
                              onChange={(e) => handleParamUpdate(
                                indicator.id, 
                                config.key, 
                                Number(e.target.value)
                              )}
                              className="h-8"
                            />
                          ) : (
                            <select
                              value={indicator.params[config.key]}
                              onChange={(e) => handleParamUpdate(
                                indicator.id,
                                config.key,
                                e.target.value
                              )}
                              className="w-full h-8 px-3 rounded-md border border-input bg-background text-sm"
                            >
                              {config.options?.map(opt => (
                                <option key={opt} value={opt}>{opt}</option>
                              ))}
                            </select>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}
      
      {/* 안내 메시지 */}
      {indicators.length === 0 && (
        <Card className="p-6 text-center">
          <p className="text-muted-foreground">
            위에서 지표를 선택하여 추가하세요.
          </p>
        </Card>
      )}
    </div>
  );
}

