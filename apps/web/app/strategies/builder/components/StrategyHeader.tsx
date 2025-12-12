/**
 * 전략 헤더 컴포넌트
 * 
 * 전략 이름, 설명 입력 및 저장/실행 버튼 제공
 */

'use client';

import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { AlertCircle, Save, Play } from 'lucide-react';
import type { StrategyDraft, ValidationError } from '@/types/strategy-draft';

interface StrategyHeaderProps {
  draft: StrategyDraft;
  updateDraft: (updater: (draft: StrategyDraft) => StrategyDraft) => void;
  onSave: () => void;
  errors: ValidationError[];
  isSaving?: boolean;
}

/**
 * 전략 헤더
 * 
 * 전략의 기본 정보(이름, 설명)를 입력받고
 * 저장/실행 버튼을 제공
 */
export function StrategyHeader({ 
  draft, 
  updateDraft, 
  onSave,
  errors,
  isSaving = false
}: StrategyHeaderProps) {
  
  // 저장 가능 여부 (에러가 없어야 함)
  const canSave = errors.length === 0 && draft.name.trim().length > 0 && !isSaving;
  
  return (
    <div className="space-y-4">
      {/* 기본 정보 입력 */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="strategy-name">
              전략 이름 <span className="text-destructive">*</span>
            </Label>
            <Input
              id="strategy-name"
              placeholder="예: Simple EMA Cross Strategy"
              value={draft.name}
              onChange={(e) => updateDraft(d => ({ ...d, name: e.target.value }))}
              className={errors.some(e => e.field === 'name') ? 'border-destructive' : ''}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="strategy-description">
              전략 설명 (선택)
            </Label>
            <Input
              id="strategy-description"
              placeholder="전략에 대한 간단한 설명을 입력하세요"
              value={draft.description}
              onChange={(e) => updateDraft(d => ({ ...d, description: e.target.value }))}
            />
          </div>
        </div>
      </Card>
      
      {/* Validation 에러 표시 */}
      {errors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>입력 오류</AlertTitle>
          <AlertDescription>
            <ul className="list-disc pl-5 mt-2 space-y-1">
              {errors.map((err, idx) => (
                <li key={idx}>{err.message}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
      
      {/* 액션 버튼 */}
      <div className="flex gap-3">
        <Button 
          onClick={onSave}
          disabled={!canSave}
          size="lg"
        >
          <Save className="h-4 w-4 mr-2" />
          {isSaving ? '저장 중...' : '저장'}
        </Button>
        
        <Button 
          onClick={onSave}
          disabled={!canSave}
          variant="outline"
          size="lg"
        >
          <Play className="h-4 w-4 mr-2" />
          저장 후 실행
        </Button>
      </div>
    </div>
  );
}

