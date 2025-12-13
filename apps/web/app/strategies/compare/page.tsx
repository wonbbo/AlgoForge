/**
 * 전략 비교 페이지
 * 
 * 여러 전략의 성능을 비교하여 표시
 */

"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ArrowLeft, TrendingUp, TrendingDown } from "lucide-react"
import { runApi } from "@/lib/api-client"
import type { Run } from "@/lib/types"
// formatNumber 함수 로컬 정의
function formatNumber(value: number): string {
  return value.toFixed(2);
}
import Link from "next/link"

/**
 * 전략 비교 페이지 컴포넌트 (내부)
 */
function CompareStrategiesContent() {
  const searchParams = useSearchParams()
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  
  // URL에서 run_ids 가져오기 (예: ?ids=1,2,3)
  const runIds = searchParams.get('ids')?.split(',').map(Number) || []
  
  useEffect(() => {
    loadRuns()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  
  async function loadRuns() {
    if (runIds.length === 0) {
      setLoading(false)
      return
    }
    
    try {
      // 각 Run 조회
      const promises = runIds.map(id => runApi.get(id))
      const results = await Promise.all(promises)
      setRuns(results)
    } catch (error: any) {
      console.error('Failed to load runs:', error)
      toast.error('Run 정보를 불러오는데 실패했습니다', {
        description: error.message
      })
    } finally {
      setLoading(false)
    }
  }
  
  // Metrics 비교 테이블 데이터
  const metricsComparison = [
    {
      name: '총 거래 수',
      key: 'trades_count',
      format: (v: number) => v.toString()
    },
    {
      name: '승률',
      key: 'win_rate',
      format: (v: number) => `${(v * 100).toFixed(2)}%`
    },
    {
      name: '총 수익률',
      key: 'total_return',
      format: (v: number) => `${(v * 100).toFixed(2)}%`
    },
    {
      name: 'Profit Factor',
      key: 'profit_factor',
      format: (v: number) => formatNumber(v)
    },
    {
      name: 'Max Drawdown',
      key: 'max_drawdown',
      format: (v: number) => `${(v * 100).toFixed(2)}%`
    },
    {
      name: 'Sharpe Ratio',
      key: 'sharpe_ratio',
      format: (v: number | null) => v !== null ? formatNumber(v) : 'N/A'
    },
    {
      name: 'TP1 도달률',
      key: 'tp1_hit_rate',
      format: (v: number) => `${(v * 100).toFixed(2)}%`
    },
    {
      name: 'BE 청산률',
      key: 'be_exit_rate',
      format: (v: number) => `${(v * 100).toFixed(2)}%`
    }
  ]
  
  // 최고 성능 찾기
  const getBestValue = (key: string): number | null => {
    if (runs.length === 0) return null
    
    const values = runs
      .map(r => r.metrics?.[key as keyof typeof r.metrics])
      .filter(v => v !== null && v !== undefined) as number[]
    
    if (values.length === 0) return null
    
    // Max Drawdown는 작을수록 좋음
    if (key === 'max_drawdown') {
      return Math.min(...values)
    }
    
    return Math.max(...values)
  }
  
  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <p className="text-center text-muted-foreground py-8">로딩 중...</p>
      </div>
    )
  }
  
  if (runs.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>비교할 전략이 없습니다</CardTitle>
            <CardDescription>
              URL 파라미터로 비교할 Run ID를 지정해주세요.
              <br />
              예: /strategies/compare?ids=1,2,3
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/runs">
              <Button>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Run 목록으로
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto p-6 space-y-8">
      {/* 헤더 */}
      <div>
        <Link href="/runs">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            뒤로가기
          </Button>
        </Link>
        <h1 className="text-3xl font-bold mb-2">전략 비교</h1>
        <p className="text-muted-foreground">
          {runs.length}개의 전략 성능을 비교합니다.
        </p>
      </div>
      
      {/* Run 정보 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {runs.map((run) => (
          <Card key={run.run_id}>
            <CardHeader>
              <CardTitle className="text-base">Run #{run.run_id}</CardTitle>
              <CardDescription className="text-sm line-clamp-2">
                {run.strategy?.name || 'Unknown Strategy'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">상태</span>
                  <Badge variant={
                    run.status === 'COMPLETED' ? 'default' : 
                    run.status === 'RUNNING' ? 'secondary' : 'destructive'
                  }>
                    {run.status}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">수익률</span>
                  <span className={
                    (run.metrics?.total_return || 0) >= 0 
                      ? 'text-green-600 font-semibold' 
                      : 'text-red-600 font-semibold'
                  }>
                    {run.metrics?.total_return !== undefined
                      ? `${(run.metrics.total_return * 100).toFixed(2)}%`
                      : 'N/A'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {/* Metrics 비교 테이블 */}
      <Card>
        <CardHeader>
          <CardTitle>성능 지표 비교</CardTitle>
          <CardDescription>
            각 전략의 주요 성능 지표를 비교합니다. 최고 성능은 <TrendingUp className="inline h-4 w-4 text-green-600" /> 로 표시됩니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>지표</TableHead>
                {runs.map((run) => (
                  <TableHead key={run.run_id} className="text-right">
                    Run #{run.run_id}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {metricsComparison.map((metric) => {
                const bestValue = getBestValue(metric.key)
                
                return (
                  <TableRow key={metric.key}>
                    <TableCell className="font-medium">{metric.name}</TableCell>
                    {runs.map((run) => {
                      const value = run.metrics?.[metric.key as keyof typeof run.metrics]
                      const isBest = value === bestValue && bestValue !== null
                      
                      return (
                        <TableCell key={run.run_id} className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            {isBest && (
                              <TrendingUp className="h-4 w-4 text-green-600" />
                            )}
                            <span className={isBest ? 'font-semibold text-green-600' : ''}>
                              {value !== null && value !== undefined
                                ? metric.format(value as number)
                                : 'N/A'}
                            </span>
                          </div>
                        </TableCell>
                      )
                    })}
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      
      {/* 승자 */}
      <Card>
        <CardHeader>
          <CardTitle>종합 평가</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 최고 수익률 */}
            {(() => {
              const bestReturnRun = runs.reduce((best, current) => {
                const bestReturn = best.metrics?.total_return || 0
                const currentReturn = current.metrics?.total_return || 0
                return currentReturn > bestReturn ? current : best
              })
              
              return (
                <div>
                  <h3 className="text-sm font-semibold mb-2">🏆 최고 수익률</h3>
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <span className="font-medium">
                      Run #{bestReturnRun.run_id} - {bestReturnRun.strategy?.name}
                    </span>
                    <span className="text-green-600 font-bold">
                      {bestReturnRun.metrics?.total_return !== undefined
                        ? `${(bestReturnRun.metrics.total_return * 100).toFixed(2)}%`
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              )
            })()}
            
            {/* 최고 승률 */}
            {(() => {
              const bestWinRateRun = runs.reduce((best, current) => {
                const bestWinRate = best.metrics?.win_rate || 0
                const currentWinRate = current.metrics?.win_rate || 0
                return currentWinRate > bestWinRate ? current : best
              })
              
              return (
                <div>
                  <h3 className="text-sm font-semibold mb-2">🎯 최고 승률</h3>
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <span className="font-medium">
                      Run #{bestWinRateRun.run_id} - {bestWinRateRun.strategy?.name}
                    </span>
                    <span className="text-blue-600 font-bold">
                      {bestWinRateRun.metrics?.win_rate !== undefined
                        ? `${(bestWinRateRun.metrics.win_rate * 100).toFixed(2)}%`
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              )
            })()}
            
            {/* 최소 Drawdown */}
            {(() => {
              const bestDrawdownRun = runs.reduce((best, current) => {
                const bestDrawdown = Math.abs(best.metrics?.max_drawdown || Infinity)
                const currentDrawdown = Math.abs(current.metrics?.max_drawdown || Infinity)
                return currentDrawdown < bestDrawdown ? current : best
              })
              
              return (
                <div>
                  <h3 className="text-sm font-semibold mb-2">🛡️ 최소 손실폭</h3>
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <span className="font-medium">
                      Run #{bestDrawdownRun.run_id} - {bestDrawdownRun.strategy?.name}
                    </span>
                    <span className="text-purple-600 font-bold">
                      {bestDrawdownRun.metrics?.max_drawdown !== undefined
                        ? `${(bestDrawdownRun.metrics.max_drawdown * 100).toFixed(2)}%`
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              )
            })()}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * 전략 비교 페이지 (Suspense 래퍼)
 */
export default function CompareStrategiesPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto p-6">
        <p className="text-center text-muted-foreground py-8">로딩 중...</p>
      </div>
    }>
      <CompareStrategiesContent />
    </Suspense>
  )
}

