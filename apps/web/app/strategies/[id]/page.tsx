/**
 * 전략 상세 페이지
 * 
 * 전략의 상세 정보와 JSON 정의를 표시합니다.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Copy, Download, Trash2, Calendar, Hash } from 'lucide-react';
import { strategyApi } from '@/lib/api-client';
import type { Strategy } from '@/lib/types';

/**
 * 전략 상세 페이지
 */
export default function StrategyDetailPage() {
  const router = useRouter();
  const params = useParams();
  const strategyId = parseInt(params.id as string);
  
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // 전략 로드
  useEffect(() => {
    const loadStrategy = async () => {
      try {
        setIsLoading(true);
        const data = await strategyApi.get(strategyId);
        setStrategy(data);
      } catch (error: any) {
        console.error('전략 로드 실패:', error);
        toast.error('전략을 불러오는데 실패했습니다', {
          description: error.message
        });
        // 목록으로 돌아가기
        setTimeout(() => router.push('/strategies'), 2000);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadStrategy();
  }, [strategyId, router]);
  
  // JSON 복사
  const handleCopyJson = () => {
    if (!strategy) return;
    
    const jsonString = JSON.stringify(strategy.definition, null, 2);
    navigator.clipboard.writeText(jsonString);
    toast.success('JSON이 클립보드에 복사되었습니다');
  };
  
  // JSON 다운로드
  const handleDownloadJson = () => {
    if (!strategy) return;
    
    const jsonString = JSON.stringify(strategy.definition, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${strategy.name.replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('JSON 파일이 다운로드되었습니다');
  };
  
  // 전략 삭제
  const handleDelete = async () => {
    if (!strategy) return;
    
    if (!confirm(`"${strategy.name}" 전략을 삭제하시겠습니까?`)) {
      return;
    }
    
    try {
      await strategyApi.delete(strategyId);
      toast.success('전략이 삭제되었습니다');
      router.push('/strategies');
    } catch (error: any) {
      console.error('전략 삭제 실패:', error);
      toast.error('전략 삭제에 실패했습니다', {
        description: error.message
      });
    }
  };
  
  // 날짜 포맷팅 (Unix timestamp 밀리초 단위)
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          뒤로 가기
        </Button>
        <Card className="p-12 text-center">
          <p className="text-muted-foreground">전략을 불러오는 중...</p>
        </Card>
      </div>
    );
  }
  
  if (!strategy) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          뒤로 가기
        </Button>
        <Card className="p-12 text-center">
          <p className="text-muted-foreground">전략을 찾을 수 없습니다</p>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          뒤로 가기
        </Button>
        
        <Button variant="destructive" onClick={handleDelete}>
          <Trash2 className="h-4 w-4 mr-2" />
          삭제
        </Button>
      </div>
      
      {/* 기본 정보 */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <CardTitle className="text-2xl">{strategy.name}</CardTitle>
              {strategy.description && (
                <CardDescription>{strategy.description}</CardDescription>
              )}
            </div>
            <Badge variant="outline">전략 ID: {strategy.strategy_id}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 메타 정보 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Hash className="h-4 w-4" />
                  <span className="font-semibold">Strategy Hash</span>
                </div>
                <p className="font-mono text-xs break-all bg-muted p-2 rounded">
                  {strategy.strategy_hash}
                </p>
              </div>
              
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span className="font-semibold">생성일</span>
                </div>
                <p className="text-sm">{formatDate(strategy.created_at)}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* JSON 정의 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>전략 정의 (JSON)</CardTitle>
              <CardDescription>
                전략의 진입/청산 규칙이 JSON 형식으로 정의되어 있습니다
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleCopyJson}>
                <Copy className="h-4 w-4 mr-1" />
                복사
              </Button>
              <Button variant="outline" size="sm" onClick={handleDownloadJson}>
                <Download className="h-4 w-4 mr-1" />
                다운로드
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted p-4 rounded text-xs overflow-auto max-h-[600px]">
            <code>{JSON.stringify(strategy.definition, null, 2)}</code>
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}

