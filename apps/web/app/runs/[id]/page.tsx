"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { runApi, datasetApi, strategyApi } from "@/lib/api-client"
import type { Run, Metrics, Trade, Dataset, Strategy } from "@/lib/types"
import { formatTimestamp, formatCurrency, formatPercent, getGradeColor, getStatusColor } from "@/lib/utils"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ArrowLeft, TrendingUp, TrendingDown } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { EquityCurveChart } from "./components/EquityCurveChart"
import { DrawdownChart } from "./components/DrawdownChart"

/**
 * Run 상세 페이지
 */
export default function RunDetailPage() {
  const params = useParams()
  const router = useRouter()
  const runId = Number(params.id)

  const [run, setRun] = useState<Run | null>(null)
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [strategy, setStrategy] = useState<Strategy | null>(null)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Run 상세 정보를 로드하는 함수
    async function loadRunDetail() {
      try {
        const runData = await runApi.get(runId)
        setRun(runData)

        // Dataset과 Strategy 정보 로드
        const [datasetData, strategyData] = await Promise.all([
          datasetApi.get(runData.dataset_id),
          strategyApi.get(runData.strategy_id),
        ])
        setDataset(datasetData)
        setStrategy(strategyData)

        // 완료된 Run의 경우 Metrics와 Trades 로드
        if (runData.status === 'COMPLETED') {
          const [metricsData, tradesData] = await Promise.all([
            runApi.getMetrics(runId),
            runApi.getTrades(runId),
          ])
          setMetrics(metricsData)
          setTrades(tradesData)
          
          toast.success('Run 데이터를 불러왔습니다')
        }
      } catch (error: any) {
        console.error('Failed to load run detail:', error)
        toast.error('Run 데이터를 불러오는데 실패했습니다', {
          description: error.message
        })
      } finally {
        setLoading(false)
      }
    }

    if (runId) {
      loadRunDetail()
    }
  }, [runId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">로딩 중...</p>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Run을 찾을 수 없습니다</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/runs">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold mb-2">Run #{run.run_id}</h1>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <Badge className={getStatusColor(run.status)}>
                {run.status}
              </Badge>
              {run.started_at && (
                <span>• {formatTimestamp(run.started_at)}</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Run 정보 */}
      <Card>
        <CardHeader>
          <CardTitle>Run 정보</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">데이터셋</p>
              <p className="font-medium">{dataset?.name || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">전략</p>
              <p className="font-medium">{strategy?.name || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">초기 자산</p>
              <p className="font-medium">{formatCurrency(run.initial_balance)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">엔진 버전</p>
              <p className="font-medium">{run.engine_version}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics (완료된 경우만) */}
      {metrics && (
        <>
          {/* 주요 지표 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  등급
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <Badge className={`${getGradeColor(metrics.grade)} text-2xl font-bold px-4 py-2`}>
                    {metrics.grade}
                  </Badge>
                  <span className="text-2xl font-bold">{metrics.score.toFixed(1)}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  총 손익
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${metrics.total_pnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                  {formatCurrency(metrics.total_pnl)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  평균: {formatCurrency(metrics.average_pnl)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  승률
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatPercent(metrics.win_rate * 100, 1)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {metrics.winning_trades}승 / {metrics.losing_trades}패
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  TP1 도달률
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatPercent(metrics.tp1_hit_rate * 100, 1)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  총 {metrics.trades_count}개 거래
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 상세 지표 */}
          <Card>
            <CardHeader>
              <CardTitle>상세 지표</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Profit Factor</p>
                  <p className="text-lg font-medium">{metrics.profit_factor.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Max Drawdown</p>
                  <p className="text-lg font-medium text-destructive">
                    {formatCurrency(metrics.max_drawdown)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">BE 청산률</p>
                  <p className="text-lg font-medium">
                    {formatPercent(metrics.be_exit_rate * 100, 1)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 자산 변화 차트 */}
          <Card>
            <CardHeader>
              <CardTitle>자산 변화 (Equity Curve)</CardTitle>
            </CardHeader>
            <CardContent>
              <EquityCurveChart 
                trades={trades} 
                initialBalance={run.initial_balance} 
              />
            </CardContent>
          </Card>

          {/* 손실폭 차트 */}
          <Card>
            <CardHeader>
              <CardTitle>손실폭 (Drawdown)</CardTitle>
            </CardHeader>
            <CardContent>
              <DrawdownChart 
                trades={trades} 
                initialBalance={run.initial_balance} 
              />
            </CardContent>
          </Card>

          {/* 거래 내역 */}
          <Card>
            <CardHeader>
              <CardTitle>거래 내역</CardTitle>
            </CardHeader>
            <CardContent>
              {trades.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  거래 내역이 없습니다
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>방향</TableHead>
                      <TableHead>진입가</TableHead>
                      <TableHead>진입 시각</TableHead>
                      <TableHead>Legs</TableHead>
                      <TableHead className="text-right">손익</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {trades.map((trade) => (
                      <TableRow 
                        key={trade.trade_id}
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => router.push(`/runs/${runId}/trades/${trade.trade_id}`)}
                      >
                        <TableCell className="font-medium">
                          #{trade.trade_id}
                        </TableCell>
                        <TableCell>
                          <Badge variant={trade.direction === 'LONG' ? 'default' : 'secondary'}>
                            {trade.direction === 'LONG' ? (
                              <TrendingUp className="h-3 w-3 mr-1" />
                            ) : (
                              <TrendingDown className="h-3 w-3 mr-1" />
                            )}
                            {trade.direction}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {formatCurrency(trade.entry_price)}
                        </TableCell>
                        <TableCell className="text-sm">
                          {formatTimestamp(trade.entry_timestamp)}
                        </TableCell>
                        <TableCell className="text-sm">
                          {trade.legs.map(leg => leg.exit_type).join(', ')}
                        </TableCell>
                        <TableCell className={`text-right font-medium ${
                          (trade.total_pnl || 0) >= 0 ? 'text-profit' : 'text-loss'
                        }`}>
                          {formatCurrency(trade.total_pnl || 0)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* 대기/실행 중 상태 메시지 */}
      {run.status === 'PENDING' && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <p className="text-sm text-yellow-800">
              백테스트가 대기 중입니다...
            </p>
          </CardContent>
        </Card>
      )}

      {run.status === 'RUNNING' && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <p className="text-sm text-blue-800">
              백테스트가 실행 중입니다... 잠시 후 새로고침 해주세요.
            </p>
          </CardContent>
        </Card>
      )}

      {run.status === 'FAILED' && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-sm text-red-800">
              백테스트 실행에 실패했습니다.
              {run.run_artifacts?.error && (
                <span className="block mt-1 font-mono text-xs">
                  오류: {run.run_artifacts.error}
                </span>
              )}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

