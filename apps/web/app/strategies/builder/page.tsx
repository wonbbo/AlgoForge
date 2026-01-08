/**
 * 전략 빌더 메인 페이지
 * 
 * Phase 2 구현: 완전한 전략 빌더 UI
 */

'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import type { StrategyDraft, ValidationError } from '@/types/strategy-draft';
import type { Indicator } from '@/lib/types';
import { createEmptyDraft } from '@/lib/strategy-draft-utils';
import { validateDraft } from '@/lib/draft-validation';
import { draftToStrategyJSON } from '@/lib/draft-to-json';
import { strategyJSONToDraft, canConvertToDraft } from '@/lib/json-to-draft';
import { strategyApi, indicatorApi } from '@/lib/api-client';
import { StrategyHeader } from './components/StrategyHeader';
import { StepWizard } from './components/StepWizard';
import { JsonPreviewPanel } from './components/JsonPreviewPanel';
import { TemplateManager } from './components/TemplateManager';

/**
 * 로딩 폴백 컴포넌트
 */
function LoadingFallback() {
  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
          <p className="text-muted-foreground">전략 빌더 로딩 중...</p>
        </div>
      </div>
    </div>
  );
}

/**
 * 전략 빌더 페이지 래퍼
 * 
 * useSearchParams를 사용하는 컴포넌트는 Suspense로 감싸야 함
 */
export default function StrategyBuilderPageWrapper() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <StrategyBuilderPage />
    </Suspense>
  );
}

/**
 * 전략 빌더 페이지
 * 
 * Draft State를 관리하고 실시간 Validation 제공
 */
function StrategyBuilderPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // URL 쿼리 파라미터에서 source 전략 ID 읽기
  const sourceStrategyId = searchParams.get('source');
  
  // Draft State
  const [draft, setDraft] = useState<StrategyDraft>(createEmptyDraft());
  
  // Validation 결과
  const [errors, setErrors] = useState<ValidationError[]>([]);
  
  // 현재 Step
  const [currentStep, setCurrentStep] = useState<string>('step1');
  
  // 저장 중 상태
  const [isSaving, setIsSaving] = useState<boolean>(false);
  
  // 소스 전략 로딩 상태
  const [isLoadingSource, setIsLoadingSource] = useState<boolean>(false);
  
  // 사용 가능한 지표 목록 (다중 출력 필드 정보 포함)
  const [availableIndicators, setAvailableIndicators] = useState<Indicator[]>([]);
  const [isLoadingIndicators, setIsLoadingIndicators] = useState<boolean>(true);
  
  // 소스 전략 로드 (복제하여 편집 기능)
  useEffect(() => {
    if (!sourceStrategyId) return;
    
    const loadSourceStrategy = async () => {
      setIsLoadingSource(true);
      try {
        const strategyIdNum = parseInt(sourceStrategyId, 10);
        if (isNaN(strategyIdNum)) {
          toast.error('잘못된 전략 ID입니다');
          return;
        }
        
        // 전략 조회
        const strategy = await strategyApi.get(strategyIdNum);
        
        // 변환 가능 여부 확인
        if (!canConvertToDraft(strategy.definition)) {
          toast.error('이 전략은 빌더에서 편집할 수 없습니다', {
            description: '지원하지 않는 스키마 버전입니다.'
          });
          return;
        }
        
        // JSON → Draft 변환 (이름에 "(복사본)" 추가)
        const loadedDraft = strategyJSONToDraft(
          strategy.definition,
          `${strategy.name} (복사본)`,
          strategy.description || ''
        );
        
        // Draft 상태 업데이트
        setDraft(loadedDraft);
        
        // Validation 실행
        const validationResult = validateDraft(loadedDraft);
        setErrors(validationResult.errors);
        
        // 알림
        toast.success('전략을 불러왔습니다', {
          description: '수정 후 새 전략으로 저장됩니다.'
        });
        
        console.log('[Builder] 소스 전략 로드 완료:', strategy.name);
        
      } catch (err: any) {
        console.error('소스 전략 로드 실패:', err);
        toast.error('전략을 불러오는데 실패했습니다', {
          description: err.message || '서버와의 통신에 실패했습니다.'
        });
      } finally {
        setIsLoadingSource(false);
      }
    };
    
    loadSourceStrategy();
  }, [sourceStrategyId]);
  
  // 지표 목록 로드
  useEffect(() => {
    const loadIndicators = async () => {
      setIsLoadingIndicators(true);
      try {
        const data = await indicatorApi.list();
        // indicatorApi.list()는 이미 배열을 반환함 (response.indicators)
        console.log('[Builder] 지표 목록 로드 완료:', data.length, '개');
        console.log('[Builder] 커스텀 지표:', data.filter(i => i.implementation_type === 'custom').map(i => ({
          type: i.type,
          output_fields: i.output_fields
        })));
        setAvailableIndicators(data);
      } catch (err: any) {
        console.error('지표 목록 로드 실패:', err);
        // 에러가 발생해도 빌더는 계속 사용 가능 (지표 선택만 제한됨)
      } finally {
        setIsLoadingIndicators(false);
      }
    };
    loadIndicators();
  }, []);
  
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
  
  // 소스 전략 로딩 중 화면
  if (isLoadingSource) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
            <p className="text-muted-foreground">전략을 불러오는 중...</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-6">
      {/* 헤더 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">전략 빌더</h1>
            <p className="text-muted-foreground mt-2">
              {sourceStrategyId 
                ? '기존 전략을 기반으로 새 전략을 만듭니다. 저장 시 새 전략으로 생성됩니다.'
                : 'JSON 지식 없이도 직관적으로 전략을 만들 수 있습니다.'
              }
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
            availableIndicators={availableIndicators}
            isLoadingIndicators={isLoadingIndicators}
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
