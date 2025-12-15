/**
 * Hook 설정 컴포넌트
 * 
 * 진입 필터(Hook) 설정을 관리
 */

'use client';

import { Card } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Settings, AlertCircle } from 'lucide-react';
import type { HookDraft } from '@/types/strategy-draft';

interface HookSettingsProps {
  hook: HookDraft;
  onUpdate: (hook: HookDraft) => void;
}

/**
 * Hook 설정 컴포넌트
 * 
 * MVP에서는 비활성화, v2에서 구현 예정
 */
export function HookSettings({
  hook,
  onUpdate
}: HookSettingsProps) {
  
  return (
    <Card className="p-5">
      <div className="space-y-4">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-lg">Hook (진입 필터)</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              진입 조건에 추가 필터를 적용하여 진입을 허용/차단
            </p>
          </div>
          
          {/* 활성화 스위치 (비활성화됨) */}
          <Switch
            id="hook-enabled"
            checked={hook.enabled}
            onCheckedChange={(checked) => {
              onUpdate({ enabled: checked });
            }}
            disabled={true}
          />
        </div>
        
        {/* MVP 제약 안내 */}
        <Alert variant="default" className="bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800">
          <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          <AlertDescription className="text-sm text-amber-900 dark:text-amber-100">
            <p className="font-medium mb-1">v2에서 지원 예정</p>
            <p>
              Hook 기능은 현재 MVP 버전에서 비활성화되어 있습니다. 
              향후 버전에서 다양한 진입 필터(볼륨, 변동성, 시간대 등)를 추가할 예정입니다.
            </p>
          </AlertDescription>
        </Alert>
        
        {/* Hook 개념 설명 */}
        <div className="space-y-3 pt-3 border-t">
          <p className="text-sm font-medium">Hook이란?</p>
          <div className="space-y-2 text-xs text-muted-foreground">
            <p>
              Hook은 진입 조건이 만족되더라도 추가적인 조건을 확인하여 
              진입을 허용하거나 차단하는 필터입니다.
            </p>
            <p className="font-medium text-foreground mt-2">예시 (v2에서 구현 예정):</p>
            <ul className="space-y-1 pl-4 list-disc">
              <li>볼륨 필터: 거래량이 평균의 1.5배 이상일 때만 진입</li>
              <li>변동성 필터: ATR이 일정 범위 내일 때만 진입</li>
              <li>시간대 필터: 특정 시간대에만 진입 허용</li>
              <li>추세 필터: 장기 추세와 일치할 때만 진입</li>
            </ul>
          </div>
        </div>
        
        {/* 제약 사항 */}
        <div className="pt-3 border-t">
          <p className="text-xs text-muted-foreground">
            ⚠️ <strong>중요:</strong> Hook은 진입 허용/차단만 가능하며, 
            가격·사이즈·SL/TP를 조작할 수 없습니다.
          </p>
        </div>
      </div>
    </Card>
  );
}

