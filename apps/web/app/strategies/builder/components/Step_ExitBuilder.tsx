/**
 * 진출 조건 구성 컴포넌트
 * 
 * 지표 기반 진출 조건과 ATR Trailing Stop을 설정
 * 둘 다 선택사항이며, 둘 다 비활성화하면 기존 동작 유지 (반대 진입 신호로 청산)
 */

'use client';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, TrendingUp, TrendingDown, LineChart, Activity } from 'lucide-react';
import { ConditionRow } from './ConditionRow';
import { createEmptyCondition } from '@/lib/strategy-draft-utils';
import type { ExitDraft, IndicatorDraft, ConditionDraft } from '@/types/strategy-draft';
import type { Indicator } from '@/lib/types';

interface StepExitProps {
  exit: ExitDraft;
  indicators: IndicatorDraft[];
  availableIndicators: Indicator[];
  isLoadingIndicators: boolean;
  onUpdateExit: (exit: ExitDraft) => void;
}

/**
 * 진출 조건 구성 컴포넌트
 * 
 * 1. 지표 기반 진출 조건: 예) close가 ema200에 닿으면 청산
 * 2. ATR Trailing Stop: TP1 달성 후 동적 손절선 적용
 */
export function Step_ExitBuilder({
  exit,
  indicators,
  availableIndicators,
  isLoadingIndicators,
  onUpdateExit
}: StepExitProps) {
  
  // ATR 지표만 필터링 (ATR Trailing용)
  const atrIndicators = indicators.filter(i => i.type === 'atr');
  
  // === 지표 기반 진출 조건 핸들러 ===
  
  // 지표 기반 진출 활성화/비활성화 토글
  const handleToggleIndicatorBased = (enabled: boolean) => {
    onUpdateExit({
      ...exit,
      indicatorBased: {
        ...exit.indicatorBased,
        enabled
      }
    });
  };
  
  // 롱 청산 조건 추가
  const handleAddLongExitCondition = () => {
    const newCondition = createEmptyCondition();
    onUpdateExit({
      ...exit,
      indicatorBased: {
        ...exit.indicatorBased,
        long: {
          conditions: [...exit.indicatorBased.long.conditions, newCondition]
        }
      }
    });
  };
  
  // 숏 청산 조건 추가
  const handleAddShortExitCondition = () => {
    const newCondition = createEmptyCondition();
    onUpdateExit({
      ...exit,
      indicatorBased: {
        ...exit.indicatorBased,
        short: {
          conditions: [...exit.indicatorBased.short.conditions, newCondition]
        }
      }
    });
  };
  
  // 롱 청산 조건 업데이트
  const handleUpdateLongExitCondition = (index: number, updated: ConditionDraft) => {
    const newConditions = [...exit.indicatorBased.long.conditions];
    newConditions[index] = updated;
    onUpdateExit({
      ...exit,
      indicatorBased: {
        ...exit.indicatorBased,
        long: { conditions: newConditions }
      }
    });
  };
  
  // 숏 청산 조건 업데이트
  const handleUpdateShortExitCondition = (index: number, updated: ConditionDraft) => {
    const newConditions = [...exit.indicatorBased.short.conditions];
    newConditions[index] = updated;
    onUpdateExit({
      ...exit,
      indicatorBased: {
        ...exit.indicatorBased,
        short: { conditions: newConditions }
      }
    });
  };
  
  // 롱 청산 조건 삭제
  const handleRemoveLongExitCondition = (index: number) => {
    onUpdateExit({
      ...exit,
      indicatorBased: {
        ...exit.indicatorBased,
        long: {
          conditions: exit.indicatorBased.long.conditions.filter((_, i) => i !== index)
        }
      }
    });
  };
  
  // 숏 청산 조건 삭제
  const handleRemoveShortExitCondition = (index: number) => {
    onUpdateExit({
      ...exit,
      indicatorBased: {
        ...exit.indicatorBased,
        short: {
          conditions: exit.indicatorBased.short.conditions.filter((_, i) => i !== index)
        }
      }
    });
  };
  
  // === ATR Trailing Stop 핸들러 ===
  
  // ATR Trailing 활성화/비활성화 토글
  const handleToggleAtrTrailing = (enabled: boolean) => {
    onUpdateExit({
      ...exit,
      atrTrailing: {
        ...exit.atrTrailing,
        enabled
      }
    });
  };
  
  // ATR 지표 선택
  const handleSelectAtrIndicator = (indicatorId: string) => {
    onUpdateExit({
      ...exit,
      atrTrailing: {
        ...exit.atrTrailing,
        atr_indicator_id: indicatorId
      }
    });
  };
  
  // ATR 배수 변경
  const handleChangeMultiplier = (value: string) => {
    const multiplier = parseFloat(value);
    if (!isNaN(multiplier) && multiplier > 0) {
      onUpdateExit({
        ...exit,
        atrTrailing: {
          ...exit.atrTrailing,
          multiplier
        }
      });
    }
  };
  
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">진출 조건 구성</h2>
        <p className="text-muted-foreground">
          포지션 청산 조건을 설정합니다. 설정하지 않으면 기존대로 반대 진입 신호에서 청산됩니다.
        </p>
      </div>
      
      {/* 안내 메시지: 모두 비활성화 시 */}
      {!exit.indicatorBased.enabled && !exit.atrTrailing.enabled && (
        <Card className="p-4 bg-muted/50 border-dashed">
          <p className="text-sm text-muted-foreground text-center">
            진출 조건이 설정되지 않았습니다. 
            기존대로 반대 방향 진입 신호 발생 시 청산됩니다.
          </p>
        </Card>
      )}
      
      {/* 1. 지표 기반 진출 조건 */}
      <Card className="p-6">
        <div className="space-y-4">
          {/* 헤더 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <LineChart className="h-5 w-5 text-primary" />
              <div>
                <h3 className="font-semibold">지표 기반 진출</h3>
                <p className="text-sm text-muted-foreground">
                  특정 지표 조건 충족 시 포지션 청산
                </p>
              </div>
            </div>
            <Switch
              checked={exit.indicatorBased.enabled}
              onCheckedChange={handleToggleIndicatorBased}
            />
          </div>
          
          {/* 지표 기반 진출 조건 설정 (활성화 시) */}
          {exit.indicatorBased.enabled && (
            <div className="pt-4 border-t">
              {/* 지표 선택 안내 */}
              {indicators.length === 0 && (
                <Card className="p-4 bg-muted/50 mb-4">
                  <p className="text-center text-muted-foreground text-sm">
                    ⚠️ 먼저 Step 1에서 지표를 추가해주세요.
                  </p>
                </Card>
              )}
              
              {/* 롱/숏 청산 조건 탭 */}
              <Tabs defaultValue="long" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="long" className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    롱 청산 ({exit.indicatorBased.long.conditions.length})
                  </TabsTrigger>
                  <TabsTrigger value="short" className="flex items-center gap-2">
                    <TrendingDown className="h-4 w-4" />
                    숏 청산 ({exit.indicatorBased.short.conditions.length})
                  </TabsTrigger>
                </TabsList>
                
                {/* 롱 청산 조건 */}
                <TabsContent value="long" className="space-y-4">
                  <div className="space-y-3">
                    {exit.indicatorBased.long.conditions.length > 0 ? (
                      <>
                        {exit.indicatorBased.long.conditions.map((condition, index) => (
                          <div key={condition.tempId}>
                            {index > 0 && (
                              <div className="flex items-center justify-center py-2">
                                <span className="text-sm font-semibold text-muted-foreground px-3 py-1 bg-muted rounded-full">
                                  AND
                                </span>
                              </div>
                            )}
                            <ConditionRow
                              condition={condition}
                              indicators={indicators}
                              availableIndicators={availableIndicators}
                              onChange={(updated) => handleUpdateLongExitCondition(index, updated)}
                              onRemove={() => handleRemoveLongExitCondition(index)}
                            />
                          </div>
                        ))}
                      </>
                    ) : (
                      <Card className="p-4 text-center bg-muted/30">
                        <p className="text-sm text-muted-foreground">
                          롱 포지션 청산 조건이 없습니다.
                        </p>
                      </Card>
                    )}
                  </div>
                  
                  <Button 
                    onClick={handleAddLongExitCondition}
                    disabled={indicators.length === 0 || isLoadingIndicators}
                    className="w-full"
                    variant="outline"
                    size="sm"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    롱 청산 조건 추가
                  </Button>
                </TabsContent>
                
                {/* 숏 청산 조건 */}
                <TabsContent value="short" className="space-y-4">
                  <div className="space-y-3">
                    {exit.indicatorBased.short.conditions.length > 0 ? (
                      <>
                        {exit.indicatorBased.short.conditions.map((condition, index) => (
                          <div key={condition.tempId}>
                            {index > 0 && (
                              <div className="flex items-center justify-center py-2">
                                <span className="text-sm font-semibold text-muted-foreground px-3 py-1 bg-muted rounded-full">
                                  AND
                                </span>
                              </div>
                            )}
                            <ConditionRow
                              condition={condition}
                              indicators={indicators}
                              availableIndicators={availableIndicators}
                              onChange={(updated) => handleUpdateShortExitCondition(index, updated)}
                              onRemove={() => handleRemoveShortExitCondition(index)}
                            />
                          </div>
                        ))}
                      </>
                    ) : (
                      <Card className="p-4 text-center bg-muted/30">
                        <p className="text-sm text-muted-foreground">
                          숏 포지션 청산 조건이 없습니다.
                        </p>
                      </Card>
                    )}
                  </div>
                  
                  <Button 
                    onClick={handleAddShortExitCondition}
                    disabled={indicators.length === 0 || isLoadingIndicators}
                    className="w-full"
                    variant="outline"
                    size="sm"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    숏 청산 조건 추가
                  </Button>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </div>
      </Card>
      
      {/* 2. ATR Trailing Stop */}
      <Card className="p-6">
        <div className="space-y-4">
          {/* 헤더 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="h-5 w-5 text-primary" />
              <div>
                <h3 className="font-semibold">ATR Trailing Stop</h3>
                <p className="text-sm text-muted-foreground">
                  TP1 달성 후 ATR 기반 동적 손절선 적용
                </p>
              </div>
            </div>
            <Switch
              checked={exit.atrTrailing.enabled}
              onCheckedChange={handleToggleAtrTrailing}
            />
          </div>
          
          {/* ATR Trailing 설정 (활성화 시) */}
          {exit.atrTrailing.enabled && (
            <div className="pt-4 border-t space-y-4">
              {/* ATR 지표가 없는 경우 안내 */}
              {atrIndicators.length === 0 && (
                <Card className="p-4 bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
                  <p className="text-sm text-yellow-900 dark:text-yellow-100">
                    ⚠️ ATR 지표가 없습니다. Step 1에서 ATR 지표를 먼저 추가해주세요.
                  </p>
                </Card>
              )}
              
              {/* ATR 지표 선택 */}
              <div className="space-y-2">
                <Label htmlFor="atr-indicator">ATR 지표 선택</Label>
                <Select
                  value={exit.atrTrailing.atr_indicator_id}
                  onValueChange={handleSelectAtrIndicator}
                  disabled={atrIndicators.length === 0}
                >
                  <SelectTrigger id="atr-indicator">
                    <SelectValue placeholder="ATR 지표를 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    {atrIndicators.map(indicator => (
                      <SelectItem key={indicator.id} value={indicator.id}>
                        {indicator.id} (period: {indicator.params.period})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {/* ATR 배수 */}
              <div className="space-y-2">
                <Label htmlFor="atr-multiplier">ATR 배수</Label>
                <div className="flex items-center gap-2">
                  <Input
                    id="atr-multiplier"
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="10"
                    value={exit.atrTrailing.multiplier}
                    onChange={(e) => handleChangeMultiplier(e.target.value)}
                    className="w-24"
                  />
                  <span className="text-sm text-muted-foreground">× ATR</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  LONG: max(SL, Close - {exit.atrTrailing.multiplier} × ATR) / 
                  SHORT: min(SL, Close + {exit.atrTrailing.multiplier} × ATR)
                </p>
              </div>
              
              {/* 동작 설명 */}
              <Card className="p-3 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
                <p className="text-xs text-blue-900 dark:text-blue-100">
                  <strong>동작 방식:</strong><br/>
                  1. TP1 달성 시 손절선이 진입가(BE)로 이동<br/>
                  2. 이후 매 봉마다 ATR 기반으로 손절선 업데이트<br/>
                  3. 손절선은 유리한 방향으로만 이동 (불리한 방향으로는 이동 안 함)
                </p>
              </Card>
            </div>
          )}
        </div>
      </Card>
      
      {/* 안내 메시지 */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-900 dark:text-blue-100">
          💡 <strong>팁:</strong> 지표 기반 진출과 ATR Trailing Stop을 동시에 사용할 수 있습니다.
          먼저 충족되는 조건으로 청산됩니다.
        </p>
      </Card>
    </div>
  );
}
