/**
 * Step 3: 손절 방식 선택 컴포넌트
 * 
 * 손절 방식을 선택하고 파라미터 설정
 * - fixed_percent: 고정 퍼센트
 * - atr_based: ATR 기반
 * - indicator_level: 사용자 지표 기반 (가격 레벨)
 */

'use client';

import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Shield, Percent, Activity, LineChart } from 'lucide-react';
import type { StopLossDraft, IndicatorDraft } from '@/types/strategy-draft';
import type { Indicator } from '@/lib/types';

interface Step3Props {
  stopLoss: StopLossDraft;
  indicators: IndicatorDraft[];
  availableIndicators: Indicator[];
  isLoadingIndicators: boolean;
  onUpdateStopLoss: (stopLoss: StopLossDraft) => void;
}

/**
 * 지표 참조 문자열 생성
 * - 단일 출력(main만)이면 indicator_id만 반환
 * - 다중 출력이면 indicator_id.field 형태로 반환
 */
function buildIndicatorRef(indicatorId: string, field: string, outputFields: string[]): string {
  // main 필드이거나 단일 출력이면 indicator_id만 사용
  if (field === 'main' || (outputFields.length === 1 && outputFields[0] === 'main')) {
    return indicatorId;
  }
  return `${indicatorId}.${field}`;
}

/**
 * 참조 문자열에서 indicator_id와 field 추출
 */
function parseIndicatorRef(ref: string): { indicatorId: string; field: string } {
  if (!ref) return { indicatorId: '', field: 'main' };
  const parts = ref.split('.');
  if (parts.length === 1) {
    return { indicatorId: parts[0], field: 'main' };
  }
  return { indicatorId: parts[0], field: parts.slice(1).join('.') };
}

/**
 * 필드명으로 방향 추천 (low* → LONG, high* → SHORT)
 */
function suggestFieldForDirection(outputFields: string[], direction: 'long' | 'short'): string {
  if (outputFields.length === 0) return 'main';
  if (outputFields.length === 1) return outputFields[0];
  
  // LONG은 low* 포함 필드 우선, SHORT는 high* 포함 필드 우선
  const keyword = direction === 'long' ? 'low' : 'high';
  const matched = outputFields.find(f => f.toLowerCase().includes(keyword));
  return matched || outputFields[0];
}

/**
 * Step 3: 손절 방식 선택
 * 
 * fixed_percent, atr_based, indicator_level 중 선택
 */
export function Step3_StopLossSelector({
  stopLoss,
  indicators,
  availableIndicators,
  isLoadingIndicators,
  onUpdateStopLoss
}: Step3Props) {
  
  // ATR 지표 목록
  const atrIndicators = indicators.filter(i => i.type === 'atr');
  
  // 추가된 지표들의 output_fields 정보 가져오기 (API 메타데이터 기반)
  const getOutputFields = (indicatorDraft: IndicatorDraft): string[] => {
    const meta = availableIndicators.find(m => m.type === indicatorDraft.type);
    return meta?.output_fields || ['main'];
  };
  
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
          } else if (value === 'indicator_level') {
            // 첫 번째 지표를 기본으로 선택, 없으면 빈 문자열
            const firstIndicator = indicators[0];
            if (firstIndicator) {
              const outputFields = getOutputFields(firstIndicator);
              const longField = suggestFieldForDirection(outputFields, 'long');
              const shortField = suggestFieldForDirection(outputFields, 'short');
              onUpdateStopLoss({
                type: 'indicator_level',
                long_ref: buildIndicatorRef(firstIndicator.id, longField, outputFields),
                short_ref: buildIndicatorRef(firstIndicator.id, shortField, outputFields)
              });
            } else {
              onUpdateStopLoss({
                type: 'indicator_level',
                long_ref: '',
                short_ref: ''
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
        
        {/* Indicator Level (사용자 지표 기반 가격 레벨) */}
        <Card className={`p-4 cursor-pointer transition-colors ${
          stopLoss.type === 'indicator_level' ? 'border-primary bg-primary/5' : ''
        }`}>
          <div className="flex items-start gap-3">
            <RadioGroupItem 
              value="indicator_level" 
              id="indicator_level" 
              className="mt-1"
              disabled={indicators.length === 0}
            />
            <div className="flex-1 space-y-3">
              <Label 
                htmlFor="indicator_level" 
                className={`cursor-pointer ${indicators.length === 0 ? 'opacity-50' : ''}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <LineChart className="h-4 w-4" />
                  <span className="font-semibold">사용자 지표 기반 (가격 레벨)</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  지표 값 자체를 손절가로 사용 (예: SMA 채널, 볼린저 밴드)
                </p>
              </Label>
              
              {indicators.length === 0 && (
                <p className="text-sm text-amber-600 dark:text-amber-400">
                  ⚠️ 지표를 먼저 Step 1에서 추가해주세요.
                </p>
              )}
              
              {isLoadingIndicators && indicators.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  ⏳ 지표 정보를 불러오는 중...
                </p>
              )}
              
              {stopLoss.type === 'indicator_level' && indicators.length > 0 && !isLoadingIndicators && (
                <div className="space-y-4">
                  {/* LONG 손절 참조 선택 */}
                  <IndicatorRefSelector
                    label="LONG 손절 레벨"
                    description="롱 포지션의 손절가로 사용할 지표/필드"
                    ref_value={stopLoss.long_ref}
                    indicators={indicators}
                    availableIndicators={availableIndicators}
                    direction="long"
                    getOutputFields={getOutputFields}
                    onChange={(newRef) => onUpdateStopLoss({
                      ...stopLoss,
                      long_ref: newRef
                    })}
                  />
                  
                  {/* SHORT 손절 참조 선택 */}
                  <IndicatorRefSelector
                    label="SHORT 손절 레벨"
                    description="숏 포지션의 손절가로 사용할 지표/필드"
                    ref_value={stopLoss.short_ref}
                    indicators={indicators}
                    availableIndicators={availableIndicators}
                    direction="short"
                    getOutputFields={getOutputFields}
                    onChange={(newRef) => onUpdateStopLoss({
                      ...stopLoss,
                      short_ref: newRef
                    })}
                  />
                  
                  <p className="text-xs text-muted-foreground">
                    예: SMA 채널에서 LONG은 하단(low), SHORT는 상단(high) 선택
                  </p>
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

/**
 * 지표+필드 선택 컴포넌트
 * 
 * 지표와 해당 지표의 출력 필드를 선택
 */
interface IndicatorRefSelectorProps {
  label: string;
  description: string;
  ref_value: string;
  indicators: IndicatorDraft[];
  availableIndicators: Indicator[];
  direction: 'long' | 'short';
  getOutputFields: (indicator: IndicatorDraft) => string[];
  onChange: (ref: string) => void;
}

function IndicatorRefSelector({
  label,
  description,
  ref_value,
  indicators,
  availableIndicators,
  direction,
  getOutputFields,
  onChange
}: IndicatorRefSelectorProps) {
  // 현재 선택된 지표 ID와 필드 파싱
  const { indicatorId, field } = parseIndicatorRef(ref_value);
  
  // 선택된 지표의 output_fields
  const selectedIndicator = indicators.find(i => i.id === indicatorId);
  const outputFields = selectedIndicator ? getOutputFields(selectedIndicator) : ['main'];
  
  // 지표 변경 핸들러
  const handleIndicatorChange = (newIndicatorId: string) => {
    const newIndicator = indicators.find(i => i.id === newIndicatorId);
    if (!newIndicator) return;
    
    const newOutputFields = getOutputFields(newIndicator);
    const suggestedField = suggestFieldForDirection(newOutputFields, direction);
    onChange(buildIndicatorRef(newIndicatorId, suggestedField, newOutputFields));
  };
  
  // 필드 변경 핸들러
  const handleFieldChange = (newField: string) => {
    if (!selectedIndicator) return;
    const currentOutputFields = getOutputFields(selectedIndicator);
    onChange(buildIndicatorRef(indicatorId, newField, currentOutputFields));
  };
  
  // 다중 출력 지표인지 확인
  const hasMultipleOutputs = outputFields.length > 1 || (outputFields.length === 1 && outputFields[0] !== 'main');
  
  return (
    <div className="space-y-2 p-3 rounded-md bg-muted/50">
      <Label className="text-sm font-medium">{label}</Label>
      <p className="text-xs text-muted-foreground">{description}</p>
      
      <div className="flex gap-2">
        {/* 지표 선택 */}
        <select
          value={indicatorId}
          onChange={(e) => handleIndicatorChange(e.target.value)}
          className="flex-1 h-9 px-3 rounded-md border border-input bg-background text-sm"
        >
          {indicators.length === 0 && (
            <option value="">지표를 선택하세요</option>
          )}
          {indicators.map(ind => (
            <option key={ind.id} value={ind.id}>
              {ind.id} ({ind.type})
            </option>
          ))}
        </select>
        
        {/* 필드 선택 (다중 출력인 경우만) */}
        {hasMultipleOutputs && (
          <select
            value={field}
            onChange={(e) => handleFieldChange(e.target.value)}
            className="w-40 h-9 px-3 rounded-md border border-input bg-background text-sm"
          >
            {outputFields.map(f => (
              <option key={f} value={f}>
                .{f}
              </option>
            ))}
          </select>
        )}
      </div>
      
      {/* 현재 참조 표시 */}
      <p className="text-xs text-muted-foreground">
        참조: <code className="bg-muted px-1 py-0.5 rounded">{ref_value || '(선택 안됨)'}</code>
      </p>
    </div>
  );
}
