/**
 * 전략 빌더 메인 페이지
 * 
 * Phase 2 구현: 완전한 전략 빌더 UI
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import type { StrategyDraft, ValidationError } from '@/types/strategy-draft';
import { createEmptyDraft } from '@/lib/strategy-draft-utils';
import { validateDraft } from '@/lib/draft-validation';
import { draftToStrategyJSON } from '@/lib/draft-to-json';
import { strategyApi } from '@/lib/api-client';
import { StrategyHeader } from './components/StrategyHeader';
import { StepWizard } from './components/StepWizard';
import { JsonPreviewPanel } from './components/JsonPreviewPanel';
import { TemplateManager } from './components/TemplateManager';

/**
 * 전략 빌더 페이지
 * 
 * Draft State를 관리하고 실시간 Validation 제공
 */
export default function StrategyBuilderPage() {
  const router = useRouter();
  
  // Draft State
  const [draft, setDraft] = useState<StrategyDraft>(createEmptyDraft());
  
  // Validation 결과
  const [errors, setErrors] = useState<ValidationError[]>([]);
  
  // 현재 Step
  const [currentStep, setCurrentStep] = useState<string>('step1');
  
  // 저장 중 상태
  const [isSaving, setIsSaving] = useState<boolean>(false);
  
  // Draft 업데이트 핸들러
  const updateDraft = (updater: (draft: StrategyDraft) => StrategyDraft) => {
    const newDraft = updater(draft);
    setDraft(newDraft);
    
    // 실시간 Validation
    const validationResult = validateDraft(newDraft);
    setErrors(validationResult.errors);
  };
  
  // 템플릿 불러오기 핸들러
  const handleLoadTemplate = (loadedDraft: StrategyDraft) => {
    setDraft(loadedDraft);
    
    // Validation 실행
    const validationResult = validateDraft(loadedDraft);
    setErrors(validationResult.errors);
    
    // 첫 번째 Step으로 이동
    setCurrentStep('step1');
  };
  
  // 저장 핸들러
  const handleSave = async () => {
    // Validation
    const validationResult = validateDraft(draft);
    if (!validationResult.isValid) {
      setErrors(validationResult.errors);
      toast.error('입력 오류가 있습니다', {
        description: '오류 메시지를 확인하고 수정해주세요.'
      });
      return;
    }
    
    setIsSaving(true);
    
    try {
      // Draft → Strategy JSON 변환
      const strategyJSON = draftToStrategyJSON(draft);
      
      // API 호출
      const createdStrategy = await strategyApi.create({
        name: draft.name,
        description: draft.description,
        definition: strategyJSON
      });
      
      // 성공 알림
      toast.success('전략이 저장되었습니다!', {
        description: `전략 ID: ${createdStrategy.strategy_id}`
      });
      
      // 전략 목록 페이지로 이동
      setTimeout(() => {
        router.push('/strategies');
      }, 1000);
      
    } catch (error: any) {
      console.error('전략 저장 실패:', error);
      
      // 실패 알림
      toast.error('전략 저장에 실패했습니다', {
        description: error.message || '서버와의 통신에 실패했습니다.'
      });
    } finally {
      setIsSaving(false);
    }
  };
  
  return (
    <div className="container mx-auto p-6">
      {/* 헤더 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">전략 빌더</h1>
            <p className="text-muted-foreground mt-2">
              JSON 지식 없이도 직관적으로 전략을 만들 수 있습니다.
            </p>
          </div>
          
          {/* 템플릿 관리자 */}
          <TemplateManager 
            draft={draft} 
            onLoadTemplate={handleLoadTemplate}
          />
        </div>
      </div>
      
      {/* 전략 기본 정보 */}
      <StrategyHeader
        draft={draft}
        updateDraft={updateDraft}
        onSave={handleSave}
        errors={errors}
        isSaving={isSaving}
      />
      
      {/* 메인 컨텐츠: Step Wizard + JSON Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* 좌측: Step Wizard */}
        <div className="lg:col-span-2">
          <StepWizard
            draft={draft}
            updateDraft={updateDraft}
            currentStep={currentStep}
            setCurrentStep={setCurrentStep}
            errors={errors}
          />
        </div>
        
        {/* 우측: JSON Preview */}
        <div className="lg:col-span-1">
          <JsonPreviewPanel draft={draft} />
        </div>
      </div>
    </div>
  );
}
