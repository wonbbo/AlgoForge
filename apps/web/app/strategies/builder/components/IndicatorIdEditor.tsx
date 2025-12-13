/**
 * 지표 ID 수정 컴포넌트
 * 
 * 지표의 ID를 수정할 수 있는 인라인 편집기
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Check, X, Edit2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface IndicatorIdEditorProps {
  currentId: string;
  existingIds: string[];
  onUpdate: (newId: string) => void;
}

/**
 * 지표 ID 인라인 편집기
 * 
 * ID 중복 체크 및 유효성 검사 포함
 */
export function IndicatorIdEditor({
  currentId,
  existingIds,
  onUpdate
}: IndicatorIdEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [newId, setNewId] = useState(currentId);
  const [error, setError] = useState<string | null>(null);
  
  // 편집 시작
  const handleStartEdit = () => {
    setIsEditing(true);
    setNewId(currentId);
    setError(null);
  };
  
  // 편집 취소
  const handleCancel = () => {
    setIsEditing(false);
    setNewId(currentId);
    setError(null);
  };
  
  // ID 유효성 검사
  const validateId = (id: string): string | null => {
    // 빈 문자열 체크
    if (!id.trim()) {
      return 'ID는 필수입니다';
    }
    
    // 영문, 숫자, 언더스코어만 허용
    if (!/^[a-zA-Z0-9_]+$/.test(id)) {
      return 'ID는 영문, 숫자, 언더스코어(_)만 사용 가능합니다';
    }
    
    // 숫자로 시작하지 않도록
    if (/^\d/.test(id)) {
      return 'ID는 숫자로 시작할 수 없습니다';
    }
    
    // 언더스코어가 처음이나 마지막 문자, 또는 연속으로 사용되는 경우 금지
    if (id.startsWith('_') || id.endsWith('_')) {
      return 'ID는 언더스코어(_)로 시작하거나 끝날 수 없습니다';
    }
    
    if (id.includes('__')) {
      return '언더스코어(_)를 연속으로 사용할 수 없습니다';
    }
    
    // 중복 체크 (현재 ID는 제외)
    if (id !== currentId && existingIds.includes(id)) {
      return `ID "${id}"는 이미 사용 중입니다`;
    }
    
    return null;
  };
  
  // 저장
  const handleSave = () => {
    const validationError = validateId(newId);
    
    if (validationError) {
      setError(validationError);
      return;
    }
    
    // ID 업데이트
    onUpdate(newId);
    setIsEditing(false);
    setError(null);
  };
  
  // Enter 키 처리
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };
  
  if (!isEditing) {
    return (
      <div className="flex items-center gap-2">
        <span className="font-mono text-sm font-semibold text-primary">
          {currentId}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleStartEdit}
          className="h-6 w-6 p-0"
        >
          <Edit2 className="h-3 w-3" />
        </Button>
      </div>
    );
  }
  
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Input
          type="text"
          value={newId}
          onChange={(e) => {
            setNewId(e.target.value);
            setError(null);
          }}
          onKeyDown={handleKeyDown}
          className="h-8 font-mono text-sm"
          placeholder="indicator_id"
          autoFocus
        />
        <Button
          variant="ghost"
          size="sm"
          onClick={handleSave}
          className="h-8 w-8 p-0 text-green-600 hover:text-green-700 hover:bg-green-50"
        >
          <Check className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCancel}
          className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
      
      {error && (
        <Alert variant="destructive" className="py-2">
          <AlertDescription className="text-xs">
            {error}
          </AlertDescription>
        </Alert>
      )}
      
      <div className="space-y-1">
        <p className="text-xs text-muted-foreground">
          Enter: 저장 | Esc: 취소
        </p>
        <p className="text-xs text-blue-600 dark:text-blue-400">
          💡 형식: 영문, 숫자, 언더스코어(_) 사용 가능 (예: my_ema_1, custom_vol, rsi_14)
        </p>
      </div>
    </div>
  );
}

