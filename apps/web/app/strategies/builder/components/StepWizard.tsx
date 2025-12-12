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
import type { StrategyDraft, ValidationError } from '@/types/strategy-draft';

interface StepWizardProps {
  draft: StrategyDraft;
  updateDraft: (updater: (draft: StrategyDraft) => StrategyDraft) => void;
  currentStep: string;
  setCurrentStep: (step: string) => void;
  errors: ValidationError[];
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
  errors
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
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold mb-2">고급 설정</h2>
              <p className="text-muted-foreground">
                Reverse 및 Hook 설정 (선택 사항)
              </p>
            </div>
            
            {/* Reverse 설정 */}
            <Card className="p-4">
              <div className="space-y-3">
                <h3 className="font-semibold flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Reverse (반대 방향 진입)
                </h3>
                <p className="text-sm text-muted-foreground">
                  현재 포지션과 반대 방향 진입 신호 발생 시 청산 후 반대 방향으로 진입할지 여부
                </p>
                
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="reverse-enabled"
                    checked={draft.reverse.enabled}
                    onChange={(e) => {
                      updateDraft(d => ({
                        ...d,
                        reverse: e.target.checked 
                          ? { enabled: true, mode: 'use_entry_opposite' }
                          : { enabled: false }
                      }));
                    }}
                    className="h-4 w-4"
                  />
                  <label htmlFor="reverse-enabled" className="text-sm cursor-pointer">
                    Reverse 활성화 (기본값: 활성화)
                  </label>
                </div>
                
                {draft.reverse.enabled && (
                  <div className="pl-7 text-sm text-muted-foreground">
                    모드: <strong>use_entry_opposite</strong> (진입 조건의 반대 사용)
                  </div>
                )}
              </div>
            </Card>
            
            {/* Hook 설정 */}
            <Card className="p-4">
              <div className="space-y-3">
                <h3 className="font-semibold flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Hook (진입 필터)
                </h3>
                <p className="text-sm text-muted-foreground">
                  진입 조건에 추가 필터를 적용 (MVP에서는 비활성화)
                </p>
                
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="hook-enabled"
                    checked={draft.hook.enabled}
                    onChange={(e) => {
                      updateDraft(d => ({
                        ...d,
                        hook: { enabled: e.target.checked }
                      }));
                    }}
                    className="h-4 w-4"
                    disabled
                  />
                  <label htmlFor="hook-enabled" className="text-sm text-muted-foreground cursor-not-allowed">
                    Hook 활성화 (v2에서 지원 예정)
                  </label>
                </div>
              </div>
            </Card>
            
            {/* 안내 메시지 */}
            <Card className="p-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-900 dark:text-blue-100">
                💡 <strong>Tip:</strong> Reverse를 활성화하면 포지션 보유 중 반대 방향 신호 발생 시 
                기존 포지션을 청산하고 반대 방향으로 진입합니다. (롱 → 숏, 숏 → 롱)
              </p>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
}

