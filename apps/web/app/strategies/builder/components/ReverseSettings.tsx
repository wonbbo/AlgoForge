/**
 * Reverse 설정 컴포넌트
 * 
 * 반대 방향 진입 설정을 관리
 */

'use client';

import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { TrendingUp, Info } from 'lucide-react';
import type { ReverseDraft } from '@/types/strategy-draft';

interface ReverseSettingsProps {
  reverse: ReverseDraft;
  onUpdate: (reverse: ReverseDraft) => void;
}

/**
 * Reverse 설정 컴포넌트
 * 
 * 현재 포지션과 반대 방향 진입 신호 발생 시 동작을 설정
 */
export function ReverseSettings({
  reverse,
  onUpdate
}: ReverseSettingsProps) {
  
  return (
    <Card className="p-5">
      <div className="space-y-4">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-lg">Reverse (반대 방향 진입)</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              포지션 보유 중 반대 방향 신호 발생 시 청산 후 반대 방향으로 진입
            </p>
          </div>
          
          {/* 활성화 스위치 */}
          <Switch
            id="reverse-enabled"
            checked={reverse.enabled}
            onCheckedChange={(checked) => {
              onUpdate(checked 
                ? { enabled: true, mode: 'use_entry_opposite' }
                : { enabled: false }
              );
            }}
          />
        </div>
        
        {/* 활성화 상태일 때 상세 정보 */}
        {reverse.enabled && (
          <div className="space-y-3 pt-3 border-t">
            <div className="space-y-2">
              <Label className="text-sm font-medium">동작 모드</Label>
              <div className="p-3 bg-muted rounded-lg">
                <p className="text-sm font-mono">use_entry_opposite</p>
                <p className="text-xs text-muted-foreground mt-1">
                  진입 조건의 반대 방향 사용 (롱 조건 ↔ 숏 조건)
                </p>
              </div>
            </div>
            
            {/* 동작 예시 */}
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription className="text-sm">
                <p className="font-medium mb-2">동작 예시:</p>
                <ul className="space-y-1 text-xs">
                  <li>• <strong>롱 포지션 보유 중</strong> → 숏 진입 신호 발생 → 롱 청산 후 숏 진입</li>
                  <li>• <strong>숏 포지션 보유 중</strong> → 롱 진입 신호 발생 → 숏 청산 후 롱 진입</li>
                  <li>• TP1 발생 봉에서는 Reverse 신호 평가 안 함 (부분 청산 직후 재진입 방지)</li>
                </ul>
              </AlertDescription>
            </Alert>
          </div>
        )}
        
        {/* 비활성화 상태일 때 안내 */}
        {!reverse.enabled && (
          <Alert className="bg-muted">
            <Info className="h-4 w-4" />
            <AlertDescription className="text-sm">
              Reverse가 비활성화되면, 포지션 보유 중 반대 방향 신호가 발생해도
              기존 포지션을 유지하고 신호를 무시합니다.
            </AlertDescription>
          </Alert>
        )}
        
        {/* 추가 안내 */}
        <div className="pt-3 border-t">
          <p className="text-xs text-muted-foreground">
            💡 <strong>권장 설정:</strong> Reverse를 활성화하면 트렌드 변화에 빠르게 대응할 수 있지만,
            잘못된 신호로 인한 손실이 발생할 수 있습니다. 전략의 특성에 맞게 설정하세요.
          </p>
        </div>
      </div>
    </Card>
  );
}

