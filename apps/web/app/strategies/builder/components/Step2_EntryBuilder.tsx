/**
 * Step 2: 진입 조건 구성 컴포넌트
 * 
 * 롱/숏 진입 조건을 구성
 */

'use client';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, TrendingUp, TrendingDown } from 'lucide-react';
import { ConditionRow } from './ConditionRow';
import { createEmptyCondition } from '@/lib/strategy-draft-utils';
import type { EntryDraft, IndicatorDraft, ConditionDraft } from '@/types/strategy-draft';
import type { Indicator } from '@/lib/types';

interface Step2Props {
  entry: EntryDraft;
  indicators: IndicatorDraft[];
  availableIndicators: Indicator[];
  isLoadingIndicators: boolean;
  onUpdateEntry: (entry: EntryDraft) => void;
}

/**
 * Step 2: 진입 조건 구성
 * 
 * 롱/숏 진입 조건을 각각 설정
 * 각 방향은 AND 조건의 배열
 */
export function Step2_EntryBuilder({
  entry,
  indicators,
  availableIndicators,
  isLoadingIndicators,
  onUpdateEntry
}: Step2Props) {
  
  // 롱 조건 추가
  const handleAddLongCondition = () => {
    const newCondition = createEmptyCondition();
    onUpdateEntry({
      ...entry,
      long: {
        conditions: [...entry.long.conditions, newCondition]
      }
    });
  };
  
  // 숏 조건 추가
  const handleAddShortCondition = () => {
    const newCondition = createEmptyCondition();
    onUpdateEntry({
      ...entry,
      short: {
        conditions: [...entry.short.conditions, newCondition]
      }
    });
  };
  
  // 롱 조건 업데이트
  const handleUpdateLongCondition = (index: number, updated: ConditionDraft) => {
    const newConditions = [...entry.long.conditions];
    newConditions[index] = updated;
    onUpdateEntry({
      ...entry,
      long: { conditions: newConditions }
    });
  };
  
  // 숏 조건 업데이트
  const handleUpdateShortCondition = (index: number, updated: ConditionDraft) => {
    const newConditions = [...entry.short.conditions];
    newConditions[index] = updated;
    onUpdateEntry({
      ...entry,
      short: { conditions: newConditions }
    });
  };
  
  // 롱 조건 삭제
  const handleRemoveLongCondition = (index: number) => {
    onUpdateEntry({
      ...entry,
      long: {
        conditions: entry.long.conditions.filter((_, i) => i !== index)
      }
    });
  };
  
  // 숏 조건 삭제
  const handleRemoveShortCondition = (index: number) => {
    onUpdateEntry({
      ...entry,
      short: {
        conditions: entry.short.conditions.filter((_, i) => i !== index)
      }
    });
  };
  
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Step 2: 진입 조건 구성</h2>
        <p className="text-muted-foreground">
          롱(Long)과 숏(Short) 진입 조건을 각각 설정하세요. 
          여러 조건을 추가하면 AND 조건으로 결합됩니다.
        </p>
      </div>
      
      {/* 지표 선택 안내 */}
      {indicators.length === 0 && (
        <Card className="p-6 bg-muted/50">
          <p className="text-center text-muted-foreground">
            ⚠️ 먼저 Step 1에서 지표를 추가해주세요.
          </p>
        </Card>
      )}
      
      {/* 지표 메타 정보 로딩 안내 */}
      {indicators.length > 0 && isLoadingIndicators && (
        <Card className="p-6 bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
          <p className="text-center text-yellow-900 dark:text-yellow-100">
            ⏳ 지표 정보를 불러오는 중입니다... 잠시만 기다려주세요.
          </p>
        </Card>
      )}
      
      {/* 롱/숏 조건 탭 */}
      <Tabs defaultValue="long" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="long" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            롱 진입 ({entry.long.conditions.length})
          </TabsTrigger>
          <TabsTrigger value="short" className="flex items-center gap-2">
            <TrendingDown className="h-4 w-4" />
            숏 진입 ({entry.short.conditions.length})
          </TabsTrigger>
        </TabsList>
        
        {/* 롱 조건 */}
        <TabsContent value="long" className="space-y-4">
          <div className="space-y-3">
            {entry.long.conditions.length > 0 ? (
              <>
                {entry.long.conditions.map((condition, index) => (
                  <div key={condition.tempId}>
                    {index > 0 && (
                      <div className="flex items-center justify-center py-2">
                        <span className="text-sm font-semibold text-muted-foreground px-3 py-1 bg-muted rounded-full">
                          AND
                        </span>
                      </div>
                    )}
                    <ConditionRow
                      condition={condition}
                      indicators={indicators}
                      availableIndicators={availableIndicators}
                      onChange={(updated) => handleUpdateLongCondition(index, updated)}
                      onRemove={() => handleRemoveLongCondition(index)}
                    />
                  </div>
                ))}
              </>
            ) : (
              <Card className="p-6 text-center">
                <p className="text-muted-foreground">
                  롱 진입 조건이 없습니다. 아래 버튼을 클릭하여 조건을 추가하세요.
                </p>
              </Card>
            )}
          </div>
          
          <Button 
            onClick={handleAddLongCondition}
            disabled={indicators.length === 0 || isLoadingIndicators}
            className="w-full"
            variant="outline"
          >
            <Plus className="h-4 w-4 mr-2" />
            롱 조건 추가
          </Button>
        </TabsContent>
        
        {/* 숏 조건 */}
        <TabsContent value="short" className="space-y-4">
          <div className="space-y-3">
            {entry.short.conditions.length > 0 ? (
              <>
                {entry.short.conditions.map((condition, index) => (
                  <div key={condition.tempId}>
                    {index > 0 && (
                      <div className="flex items-center justify-center py-2">
                        <span className="text-sm font-semibold text-muted-foreground px-3 py-1 bg-muted rounded-full">
                          AND
                        </span>
                      </div>
                    )}
                    <ConditionRow
                      condition={condition}
                      indicators={indicators}
                      availableIndicators={availableIndicators}
                      onChange={(updated) => handleUpdateShortCondition(index, updated)}
                      onRemove={() => handleRemoveShortCondition(index)}
                    />
                  </div>
                ))}
              </>
            ) : (
              <Card className="p-6 text-center">
                <p className="text-muted-foreground">
                  숏 진입 조건이 없습니다. 아래 버튼을 클릭하여 조건을 추가하세요.
                </p>
              </Card>
            )}
          </div>
          
          <Button 
            onClick={handleAddShortCondition}
            disabled={indicators.length === 0 || isLoadingIndicators}
            className="w-full"
            variant="outline"
          >
            <Plus className="h-4 w-4 mr-2" />
            숏 조건 추가
          </Button>
        </TabsContent>
      </Tabs>
      
      {/* 안내 메시지 */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-900 dark:text-blue-100">
          💡 <strong>팁:</strong> 조건은 모두 AND로 결합됩니다. 
          예를 들어 &quot;EMA fast {'>'} EMA slow AND RSI {'<'} 30&quot;처럼 모든 조건이 동시에 만족되어야 진입합니다.
        </p>
      </Card>
    </div>
  );
}

