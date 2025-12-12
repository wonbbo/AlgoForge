/**
 * Step 4: 고급 설정 컴포넌트
 * 
 * Reverse 및 Hook 설정을 통합
 */

'use client';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Lightbulb } from 'lucide-react';
import { ReverseSettings } from './ReverseSettings';
import { HookSettings } from './HookSettings';
import type { StrategyDraft } from '@/types/strategy-draft';

interface Step4Props {
  draft: StrategyDraft;
  onUpdateReverse: (reverse: StrategyDraft['reverse']) => void;
  onUpdateHook: (hook: StrategyDraft['hook']) => void;
}

/**
 * Step 4: 고급 설정
 * 
 * Reverse와 Hook을 설정하는 선택적 단계
 */
export function Step4_Advanced({
  draft,
  onUpdateReverse,
  onUpdateHook
}: Step4Props) {
  
  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h2 className="text-2xl font-bold mb-2">고급 설정 (선택 사항)</h2>
        <p className="text-muted-foreground">
          Reverse 및 Hook 설정으로 전략을 더욱 세밀하게 조정할 수 있습니다.
        </p>
      </div>
      
      {/* 안내 메시지 */}
      <Alert className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <Lightbulb className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        <AlertTitle className="text-blue-900 dark:text-blue-100">
          선택적 설정
        </AlertTitle>
        <AlertDescription className="text-sm text-blue-800 dark:text-blue-200">
          이 설정들은 선택 사항이며, 기본값으로도 전략을 실행할 수 있습니다.
          각 설정의 설명을 읽고 전략에 맞게 조정하세요.
        </AlertDescription>
      </Alert>
      
      {/* Reverse 설정 */}
      <div className="space-y-2">
        <ReverseSettings
          reverse={draft.reverse}
          onUpdate={onUpdateReverse}
        />
      </div>
      
      {/* Hook 설정 */}
      <div className="space-y-2">
        <HookSettings
          hook={draft.hook}
          onUpdate={onUpdateHook}
        />
      </div>
      
      {/* 추가 안내 */}
      <Alert>
        <AlertDescription className="text-sm">
          <p className="font-medium mb-2">💡 설정 가이드:</p>
          <ul className="space-y-1 text-xs">
            <li>
              <strong>Reverse 활성화 권장:</strong> 대부분의 트렌드 추종 전략에 유용합니다.
              단, 레인지 시장에서는 손실이 증가할 수 있으니 백테스트로 확인하세요.
            </li>
            <li>
              <strong>Hook은 v2에서:</strong> 현재는 비활성화되어 있으며, 
              향후 버전에서 다양한 진입 필터를 추가할 예정입니다.
            </li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );
}

