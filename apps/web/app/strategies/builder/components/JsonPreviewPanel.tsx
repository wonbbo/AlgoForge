/**
 * JSON Preview Panel 컴포넌트
 * 
 * Draft State를 실시간으로 Strategy JSON으로 변환하여 표시 (Read-only)
 */

'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Copy, Download, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';
import type { StrategyDraft } from '@/types/strategy-draft';
import { draftToStrategyJSON } from '@/lib/draft-to-json';

interface JsonPreviewPanelProps {
  draft: StrategyDraft;
}

/**
 * JSON Preview Panel
 * 
 * Draft를 실시간으로 JSON으로 변환하여 미리보기
 * 복사 및 다운로드 기능 제공
 */
export function JsonPreviewPanel({ draft }: JsonPreviewPanelProps) {
  const [copied, setCopied] = useState(false);
  
  // Draft → JSON 변환
  let jsonString = '';
  let hasError = false;
  
  try {
    const strategyJSON = draftToStrategyJSON(draft);
    jsonString = JSON.stringify(strategyJSON, null, 2);
  } catch (error) {
    hasError = true;
    jsonString = `// Validation 오류\n// ${(error as Error).message}`;
  }
  
  // 복사 핸들러
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('복사 실패:', err);
    }
  };
  
  // 다운로드 핸들러
  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${draft.name || 'strategy'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  return (
    <Card className="p-4 sticky top-6 h-fit">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold">JSON Preview</h3>
        <div className="flex gap-2">
          <Button 
            size="sm" 
            variant="outline" 
            onClick={handleCopy} 
            disabled={hasError}
          >
            {copied ? (
              <>
                <CheckCircle2 className="h-4 w-4 mr-1 text-green-600" />
                복사됨
              </>
            ) : (
              <>
                <Copy className="h-4 w-4 mr-1" />
                복사
              </>
            )}
          </Button>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={handleDownload} 
            disabled={hasError}
          >
            <Download className="h-4 w-4 mr-1" />
            다운로드
          </Button>
        </div>
      </div>
      
      {/* JSON 표시 */}
      <div className="relative">
        <pre className="bg-muted p-4 rounded text-xs overflow-auto max-h-[600px] font-mono">
          <code className={hasError ? 'text-destructive' : ''}>
            {jsonString}
          </code>
        </pre>
      </div>
      
      {/* 안내 메시지 */}
      {!hasError && (
        <div className="mt-3 text-xs text-muted-foreground">
          <p>✓ Strategy JSON Schema v1.0 준수</p>
          <p>✓ Read-only (편집 불가)</p>
        </div>
      )}
    </Card>
  );
}

