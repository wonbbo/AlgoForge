/**
 * Step Wizard 컴포넌트
 * 
 * Step 네비게이션 및 각 Step 컴포넌트 통합
 */

'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { 
  BarChart3, 
  TrendingUp, 
  Shield, 
  Settings 
} from 'lucide-react';
import { Step1_IndicatorSelector } from './Step1_IndicatorSelector';
import { Step2_EntryBuilder } from './Step2_EntryBuilder';
import { Step3_StopLossSelector } from './Step3_StopLossSelector';
import { Step4_Advanced } from './Step4_Advanced';
import type { StrategyDraft, ValidationError } from '@/types/strategy-draft';
import type { Indicator } from '@/lib/types';

interface StepWizardProps {
  draft: StrategyDraft;
  updateDraft: (updater: (draft: StrategyDraft) => StrategyDraft) => void;
  currentStep: string;
  setCurrentStep: (step: string) => void;
  errors: ValidationError[];
  availableIndicators: Indicator[];
  isLoadingIndicators: boolean;
}

/**
 * Step Wizard
 * 
 * 전략 빌더의 단계별 입력을 관리
 */
export function StepWizard({
  draft,
  updateDraft,
  currentStep,
  setCurrentStep,
  errors,
  availableIndicators,
  isLoadingIndicators
}: StepWizardProps) {
  
  return (
    <Card className="p-6">
      <Tabs value={currentStep} onValueChange={setCurrentStep}>
        {/* Step 탭 목록 */}
        <TabsList className="grid w-full grid-cols-4 mb-6">
          <TabsTrigger value="step1" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">지표</span>
          </TabsTrigger>
          <TabsTrigger value="step2" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            <span className="hidden sm:inline">진입</span>
          </TabsTrigger>
          <TabsTrigger value="step3" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            <span className="hidden sm:inline">손절</span>
          </TabsTrigger>
          <TabsTrigger value="advanced" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            <span className="hidden sm:inline">고급</span>
          </TabsTrigger>
        </TabsList>
        
        {/* Step 1: 지표 선택 */}
        <TabsContent value="step1">
          <Step1_IndicatorSelector
            indicators={draft.indicators}
            onAddIndicator={(indicator) => {
              updateDraft(d => ({
                ...d,
                indicators: [...d.indicators, indicator]
              }));
            }}
            onRemoveIndicator={(id) => {
              updateDraft(d => ({
                ...d,
                indicators: d.indicators.filter(i => i.id !== id)
              }));
            }}
            onUpdateIndicator={(id, updated) => {
              updateDraft(d => ({
                ...d,
                indicators: d.indicators.map(i => i.id === id ? updated : i)
              }));
            }}
          />
        </TabsContent>
        
        {/* Step 2: 진입 조건 */}
        <TabsContent value="step2">
          <Step2_EntryBuilder
            entry={draft.entry}
            indicators={draft.indicators}
            availableIndicators={availableIndicators}
            isLoadingIndicators={isLoadingIndicators}
            onUpdateEntry={(entry) => {
              updateDraft(d => ({ ...d, entry }));
            }}
          />
        </TabsContent>
        
        {/* Step 3: 손절 */}
        <TabsContent value="step3">
          <Step3_StopLossSelector
            stopLoss={draft.stopLoss}
            indicators={draft.indicators}
            onUpdateStopLoss={(stopLoss) => {
              updateDraft(d => ({ ...d, stopLoss }));
            }}
          />
        </TabsContent>
        
        {/* Advanced: Reverse & Hook */}
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
      </Tabs>
    </Card>
  );
}

