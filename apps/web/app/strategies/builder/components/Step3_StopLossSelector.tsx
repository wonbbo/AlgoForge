/**
 * Step 3: 손절 방식 선택 컴포넌트
 * 
 * 손절 방식을 선택하고 파라미터 설정
 */

'use client';

import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Shield, Percent, Activity } from 'lucide-react';
import type { StopLossDraft, IndicatorDraft } from '@/types/strategy-draft';

interface Step3Props {
  stopLoss: StopLossDraft;
  indicators: IndicatorDraft[];
  onUpdateStopLoss: (stopLoss: StopLossDraft) => void;
}

/**
 * Step 3: 손절 방식 선택
 * 
 * fixed_percent 또는 atr_based 선택
 */
export function Step3_StopLossSelector({
  stopLoss,
  indicators,
  onUpdateStopLoss
}: Step3Props) {
  
  // ATR 지표 목록
  const atrIndicators = indicators.filter(i => i.type === 'atr');
  
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Step 3: 손절 방식 선택</h2>
        <p className="text-muted-foreground">
          손절 방식을 선택하고 파라미터를 설정하세요.
        </p>
      </div>
      
      {/* 손절 방식 선택 */}
      <RadioGroup
        value={stopLoss.type}
        onValueChange={(value) => {
          if (value === 'fixed_percent') {
            onUpdateStopLoss({ type: 'fixed_percent', percent: 2 });
          } else if (value === 'atr_based') {
            const firstAtr = atrIndicators[0];
            if (firstAtr) {
              onUpdateStopLoss({
                type: 'atr_based',
                atr_indicator_id: firstAtr.id,
                multiplier: 2
              });
            }
          }
        }}
        className="space-y-3"
      >
        {/* Fixed Percent */}
        <Card className={`p-4 cursor-pointer transition-colors ${
          stopLoss.type === 'fixed_percent' ? 'border-primary bg-primary/5' : ''
        }`}>
          <div className="flex items-start gap-3">
            <RadioGroupItem value="fixed_percent" id="fixed_percent" className="mt-1" />
            <div className="flex-1 space-y-3">
              <Label htmlFor="fixed_percent" className="cursor-pointer">
                <div className="flex items-center gap-2 mb-1">
                  <Percent className="h-4 w-4" />
                  <span className="font-semibold">고정 퍼센트 (Fixed Percent)</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  진입가 대비 고정된 퍼센트로 손절선 설정
                </p>
              </Label>
              
              {stopLoss.type === 'fixed_percent' && (
                <div className="space-y-2">
                  <Label htmlFor="percent" className="text-sm">
                    손절 비율 (%)
                  </Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="percent"
                      type="number"
                      min={0.1}
                      max={100}
                      step={0.1}
                      value={stopLoss.percent}
                      onChange={(e) => onUpdateStopLoss({
                        type: 'fixed_percent',
                        percent: Number(e.target.value)
                      })}
                      className="max-w-[200px]"
                    />
                    <span className="text-sm text-muted-foreground">%</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    예: 2%로 설정하면 진입가 대비 2% 하락/상승 시 손절
                  </p>
                </div>
              )}
            </div>
          </div>
        </Card>
        
        {/* ATR Based */}
        <Card className={`p-4 cursor-pointer transition-colors ${
          stopLoss.type === 'atr_based' ? 'border-primary bg-primary/5' : ''
        }`}>
          <div className="flex items-start gap-3">
            <RadioGroupItem 
              value="atr_based" 
              id="atr_based" 
              className="mt-1"
              disabled={atrIndicators.length === 0}
            />
            <div className="flex-1 space-y-3">
              <Label 
                htmlFor="atr_based" 
                className={`cursor-pointer ${atrIndicators.length === 0 ? 'opacity-50' : ''}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Activity className="h-4 w-4" />
                  <span className="font-semibold">ATR 기반 (ATR Based)</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  시장 변동성(ATR)에 따라 동적으로 손절선 설정
                </p>
              </Label>
              
              {atrIndicators.length === 0 && (
                <p className="text-sm text-amber-600 dark:text-amber-400">
                  ⚠️ ATR 지표를 먼저 Step 1에서 추가해주세요.
                </p>
              )}
              
              {stopLoss.type === 'atr_based' && atrIndicators.length > 0 && (
                <div className="space-y-3">
                  {/* ATR 지표 선택 */}
                  <div className="space-y-2">
                    <Label htmlFor="atr_indicator" className="text-sm">
                      ATR 지표 선택
                    </Label>
                    <select
                      id="atr_indicator"
                      value={stopLoss.atr_indicator_id}
                      onChange={(e) => onUpdateStopLoss({
                        ...stopLoss,
                        atr_indicator_id: e.target.value
                      })}
                      className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm"
                    >
                      {atrIndicators.map(atr => (
                        <option key={atr.id} value={atr.id}>
                          {atr.id} (period: {atr.params.period})
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Multiplier */}
                  <div className="space-y-2">
                    <Label htmlFor="multiplier" className="text-sm">
                      ATR 배수 (Multiplier)
                    </Label>
                    <div className="flex items-center gap-2">
                      <Input
                        id="multiplier"
                        type="number"
                        min={0.1}
                        max={10}
                        step={0.1}
                        value={stopLoss.multiplier}
                        onChange={(e) => onUpdateStopLoss({
                          ...stopLoss,
                          multiplier: Number(e.target.value)
                        })}
                        className="max-w-[200px]"
                      />
                      <span className="text-sm text-muted-foreground">× ATR</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      예: 2로 설정하면 진입가 대비 ATR의 2배 거리에 손절선 설정
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>
      </RadioGroup>
      
      {/* 안내 메시지 */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-2">
          <Shield className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div className="space-y-1">
            <p className="text-sm font-semibold text-blue-900 dark:text-blue-100">
              리스크 관리 정책
            </p>
            <p className="text-sm text-blue-800 dark:text-blue-200">
              • 기본 설정: 초기 자산의 2% 손실 제한<br />
              • Risk Reward Ratio: 1:1.5 (TP1 = 3%, BE 이동)<br />
              • TP1 도달 시 50% 청산, 나머지는 BE에서 관리
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}

