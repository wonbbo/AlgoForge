/**
 * Step 1: 지표 선택 컴포넌트
 * 
 * 카드 기반 UI로 지표를 선택하고 추가
 * API에서 내장 지표 + 커스텀 지표를 동적으로 불러옵니다.
 */

'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, TrendingUp, Activity, BarChart3, Volume2, Loader2, AlertCircle } from 'lucide-react';
import { IndicatorIdEditor } from './IndicatorIdEditor';
import { indicatorApi } from '@/lib/api-client';
import type { IndicatorDraft } from '@/types/strategy-draft';
import type { Indicator } from '@/lib/types';

interface Step1Props {
  indicators: IndicatorDraft[];
  onAddIndicator: (indicator: IndicatorDraft) => void;
  onRemoveIndicator: (id: string) => void;
  onUpdateIndicator: (id: string, updatedIndicator: IndicatorDraft) => void;
}

// 카테고리별 아이콘 매핑
const getCategoryIcon = (category: string) => {
  switch(category.toLowerCase()) {
    case 'trend': return TrendingUp;
    case 'momentum': return Activity;
    case 'volatility': return BarChart3;
    case 'volume': return Volume2;
    default: return Activity;
  }
};

// params_schema를 파싱하여 기본값 추출
const parseDefaultParams = (paramsSchema?: string): Record<string, any> => {
  if (!paramsSchema) return {};
  
  try {
    return JSON.parse(paramsSchema);
  } catch {
    return {};
  }
};

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
  // API에서 지표 목록 로드
  const [availableIndicators, setAvailableIndicators] = useState<Indicator[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    loadIndicators();
  }, []);
  
  const loadIndicators = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await indicatorApi.list();
      setAvailableIndicators(data);
    } catch (err: any) {
      console.error('지표 목록 로드 실패:', err);
      setError('지표 목록을 불러올 수 없습니다. API 서버를 확인해주세요.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // 지표 추가 핸들러
  const handleAddIndicator = (indicator: Indicator) => {
    // 자동 ID 생성 (타입_순번)
    const count = indicators.filter(i => i.type === indicator.type).length;
    const id = `${indicator.type}_${count + 1}`;
    
    const defaultParams = parseDefaultParams(indicator.params_schema);
    
    const newIndicator: IndicatorDraft = {
      id,
      type: indicator.type,
      params: { ...defaultParams }
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
      
      {/* 로딩 상태 */}
      {isLoading && (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      )}
      
      {/* 에러 상태 */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive rounded-lg">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="flex-1">{error}</p>
          <Button variant="outline" size="sm" onClick={loadIndicators}>
            재시도
          </Button>
        </div>
      )}
      
      {/* 지표 카탈로그 */}
      {!isLoading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {availableIndicators.map(indicator => {
            const Icon = getCategoryIcon(indicator.category);
            return (
              <Card key={indicator.type} className="p-4 hover:border-primary transition-colors">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className="h-5 w-5 text-primary" />
                      <h3 className="font-semibold">{indicator.name}</h3>
                      {indicator.implementation_type === 'custom' && (
                        <Badge variant="secondary" className="text-xs">커스텀</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mb-1">
                      {indicator.description || '설명 없음'}
                    </p>
                    <div className="flex items-center gap-2">
                      <p className="text-xs text-muted-foreground">
                        카테고리: {indicator.category}
                      </p>
                      {indicator.output_fields.length > 1 && (
                        <Badge variant="outline" className="text-xs">
                          {indicator.output_fields.length} 출력
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Button 
                    size="sm" 
                    onClick={() => handleAddIndicator(indicator)}
                    className="ml-2"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}
      
      {/* 추가된 지표 목록 */}
      {indicators.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-lg">추가된 지표 ({indicators.length})</h3>
          <div className="space-y-3">
            {indicators.map(indicator => {
              const indicatorInfo = availableIndicators.find(i => i.type === indicator.type);
              if (!indicatorInfo) return null;
              
              const params = parseDefaultParams(indicatorInfo.params_schema);
              
              return (
                <Card key={indicator.id} className="p-4">
                  <div className="space-y-3">
                    {/* 지표 헤더 */}
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-2 flex-1">
                        {/* ID 편집기 */}
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
                        <span className="text-sm text-muted-foreground">-</span>
                        <span className="text-sm font-medium">
                          {indicatorInfo.name}
                        </span>
                        {indicatorInfo.implementation_type === 'custom' && (
                          <Badge variant="secondary" className="text-xs">커스텀</Badge>
                        )}
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
                    {Object.keys(params).length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {Object.entries(params).map(([key, defaultValue]) => {
                          const currentValue = indicator.params[key] ?? defaultValue;
                          const valueType = typeof defaultValue;
                          
                          return (
                            <div key={key} className="space-y-1">
                              <Label className="text-xs capitalize">{key}</Label>
                              {valueType === 'number' ? (
                                <Input
                                  type="number"
                                  value={currentValue}
                                  onChange={(e) => handleParamUpdate(
                                    indicator.id, 
                                    key, 
                                    Number(e.target.value)
                                  )}
                                  className="h-8"
                                />
                              ) : valueType === 'string' && ['close', 'open', 'high', 'low', 'volume'].includes(String(defaultValue)) ? (
                                <select
                                  value={currentValue}
                                  onChange={(e) => handleParamUpdate(
                                    indicator.id,
                                    key,
                                    e.target.value
                                  )}
                                  className="w-full h-8 px-3 rounded-md border border-input bg-background text-sm"
                                >
                                  {['close', 'open', 'high', 'low', 'volume'].map(opt => (
                                    <option key={opt} value={opt}>{opt}</option>
                                  ))}
                                </select>
                              ) : (
                                <Input
                                  type="text"
                                  value={String(currentValue)}
                                  onChange={(e) => handleParamUpdate(
                                    indicator.id,
                                    key,
                                    e.target.value
                                  )}
                                  className="h-8"
                                />
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">파라미터 없음</p>
                    )}
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

