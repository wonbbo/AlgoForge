"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { runApi } from "@/lib/api-client"
import type { Trade, ChartDataResponse, Run } from "@/lib/types"
import { formatTimestamp, formatCurrency, formatPercent, formatPrice, formatNumber } from "@/lib/utils"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ArrowLeft, TrendingUp, TrendingDown, Settings } from "lucide-react"
import Link from "next/link"
import { TradeChart } from "./components/TradeChart"
import { ChartConfigModal } from "./components/ChartConfigModal"
import { ChartTypePreview } from "./components/ChartTypePreview"

/**
 * Trade 상세 페이지
 * 
 * 개별 거래의 상세 정보 및 Leg 내역을 표시합니다.
 */
export default function TradeDetailPage() {
  const params = useParams()
  const router = useRouter()
  const runId = Number(params.id)
  const tradeId = Number(params.tradeId)

  const [trade, setTrade] = useState<Trade | null>(null)
  const [run, setRun] = useState<Run | null>(null)
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [chartLoading, setChartLoading] = useState(true)
  const [chartConfigModalOpen, setChartConfigModalOpen] = useState(false)
  const [editingIndicatorKey, setEditingIndicatorKey] = useState<string>('')

  useEffect(() => {
    let isMounted = true
    
    async function loadTradeDetail() {
      try {
        // Run 정보와 Trade 정보를 함께 로드
        const [runData, tradesResponse] = await Promise.all([
          runApi.get(runId),
          runApi.getTrades(runId)
        ])
        
        if (!isMounted) return
        
        setRun(runData)
        
        const foundTrade = tradesResponse.find(t => t.trade_id === tradeId)
        
        if (!foundTrade) {
          console.error('Trade not found')
          setTrade(null)
        } else {
          setTrade(foundTrade)
        }
      } catch (error) {
        if (!isMounted) return
        console.error('Failed to load trade detail:', error)
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    async function loadChartData() {
      try {
        const data = await runApi.getTradeChartData(runId, tradeId)
        
        if (!isMounted) return
        
        // 디버깅: indicator_chart_config 확인
        console.log('Chart data loaded:', {
          indicators: Object.keys(data.indicators || {}),
          indicator_chart_config: data.indicator_chart_config,
          indicator_chart_config_keys: Object.keys(data.indicator_chart_config || {})
        })
        setChartData(data)
      } catch (error) {
        if (!isMounted) return
        console.error('Failed to load chart data:', error)
      } finally {
        if (isMounted) {
          setChartLoading(false)
        }
      }
    }

    if (runId && tradeId) {
      loadTradeDetail()
      loadChartData()
    }
    
    return () => {
      isMounted = false
    }
  }, [runId, tradeId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">로딩 중...</p>
      </div>
    )
  }

  if (!trade) {
    return (
      <div className="flex items-center justify-center py-12 flex-col space-y-4">
        <p className="text-muted-foreground">Trade를 찾을 수 없습니다</p>
        <Link href={`/runs/${runId}`}>
          <Button>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Run 상세로 돌아가기
          </Button>
        </Link>
      </div>
    )
  }

  // PnL 색상
  const pnlColor = (trade.total_pnl || 0) >= 0 ? 'text-profit' : 'text-loss'
  
  // 승패 판정
  const isWinning = (trade.total_pnl || 0) > 0

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href={`/runs/${runId}`}>
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold mb-2">Trade #{trade.trade_id}</h1>
            <div className="flex items-center space-x-2">
              <Badge variant={trade.direction === 'LONG' ? 'default' : 'secondary'}>
                {trade.direction === 'LONG' ? (
                  <TrendingUp className="h-3 w-3 mr-1" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-1" />
                )}
                {trade.direction}
              </Badge>
              <Badge className={isWinning ? 'bg-profit' : 'bg-loss'}>
                {isWinning ? '승' : '패'}
              </Badge>
              {trade.legs.some(leg => leg.exit_type === 'TP1') && (
                <Badge variant="outline" className="border-blue-500 text-blue-500">
                  TP1 도달
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 진입 정보 */}
      <Card>
        <CardHeader>
          <CardTitle>진입 정보</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 첫 번째 줄 */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">진입 시각</p>
                <p className="font-medium">{formatTimestamp(trade.entry_timestamp)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">진입가</p>
                <p className="font-medium font-mono">{formatPrice(trade.entry_price)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">포지션 크기</p>
                <p className="font-medium">{formatNumber(trade.position_size)} 계약</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">레버리지</p>
                <p className="font-medium text-blue-600 dark:text-blue-400">
                  {trade.leverage ? Math.round(trade.leverage) + 'x' : '1x'}
                </p>
              </div>
            </div>
            
            {/* 두 번째 줄 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t">
              <div>
                <p className="text-sm text-muted-foreground">매수 규모</p>
                <p className="text-xl font-bold font-mono text-primary">
                  {formatCurrency(trade.entry_price * trade.position_size)}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  진입가 × 포지션 크기
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">리스크 제한</p>
                <p className="text-xl font-bold text-orange-600 dark:text-orange-500">
                  {trade.balance_at_entry 
                    ? formatCurrency(trade.balance_at_entry * 0.02)
                    : (run ? formatCurrency(run.initial_balance * 0.02) : '-')
                  }
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  진입 시점 자산의 2%
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">초기 리스크</p>
                <p className="text-xl font-bold text-destructive font-mono">
                  ${trade.initial_risk.toFixed(4)}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  실제 리스크 금액
                </p>
              </div>
            </div>
            
            {/* 세 번째 줄 - 잔고 정보 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t">
              <div>
                <p className="text-sm text-muted-foreground">초기 잔고</p>
                <p className="text-lg font-bold font-mono">
                  {run ? formatCurrency(run.initial_balance) : '-'}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  백테스트 시작 시점
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">진입 시점 잔고</p>
                <p className="text-lg font-bold font-mono text-blue-600 dark:text-blue-400">
                  {trade.balance_at_entry 
                    ? formatCurrency(trade.balance_at_entry)
                    : (run ? formatCurrency(run.initial_balance) : '-')
                  }
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  거래 진입 시점의 자산
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">청산 시점 잔고</p>
                <p className={`text-lg font-bold font-mono ${
                  (trade.balance_at_entry || (run?.initial_balance || 0)) + (trade.total_pnl || 0) >= (trade.balance_at_entry || (run?.initial_balance || 0))
                    ? 'text-profit' 
                    : 'text-loss'
                }`}>
                  {(() => {
                    const entryBalance = trade.balance_at_entry || run?.initial_balance || 0
                    const exitBalance = entryBalance + (trade.total_pnl || 0)
                    return formatCurrency(exitBalance)
                  })()}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  진입 잔고 + 총 손익
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 손절/익절 설정 */}
      <Card>
        <CardHeader>
          <CardTitle>손절/익절 설정</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">손절가 (SL)</p>
              <p className="font-medium font-mono text-destructive">
                {formatPrice(trade.stop_loss)}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {trade.direction === 'LONG' 
                  ? `${formatPercent(((trade.entry_price - trade.stop_loss) / trade.entry_price) * 100, 2)} 하락`
                  : `${formatPercent(((trade.stop_loss - trade.entry_price) / trade.entry_price) * 100, 2)} 상승`
                }
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">1차 익절가 (TP1)</p>
              <p className="font-medium font-mono text-profit">
                {formatPrice(trade.take_profit_1)}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {trade.direction === 'LONG' 
                  ? `${formatPercent(((trade.take_profit_1 - trade.entry_price) / trade.entry_price) * 100, 2)} 상승`
                  : `${formatPercent(((trade.entry_price - trade.take_profit_1) / trade.entry_price) * 100, 2)} 하락`
                }
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 거래 결과 */}
      <Card>
        <CardHeader>
          <CardTitle>거래 결과</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">총 손익</p>
              <p className={`text-3xl font-bold ${pnlColor}`}>
                {formatCurrency(trade.total_pnl || 0)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">손익률</p>
              <p className={`text-2xl font-bold ${pnlColor}`}>
                {(() => {
                  // 진입 금액 = 진입가 × 포지션 크기
                  const entryValue = trade.entry_price * trade.position_size
                  if (entryValue > 0) {
                    return formatPercent(((trade.total_pnl || 0) / entryValue) * 100, 2)
                  }
                  return '0.00%'
                })()}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">청산 방식</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {trade.legs.map((leg, idx) => (
                  <Badge key={idx} variant="outline">
                    {leg.exit_type} ({formatPercent(leg.qty_ratio * 100, 0)})
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 차트 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>거래 차트</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {chartLoading ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">차트 로딩 중...</p>
            </div>
          ) : chartData ? (
            <>
              <div className="mb-4 space-y-2">
                {chartData.indicators && Object.keys(chartData.indicators).length > 0 ? (
                  Object.keys(chartData.indicators).map((indicatorKey) => {
                    const config = chartData.indicator_chart_config?.[indicatorKey] || null
                    // 디버깅: 각 지표의 config 확인
                    if (!config) {
                      console.warn(`지표 ${indicatorKey}의 chart_config를 찾을 수 없습니다.`, {
                        indicator_chart_config: chartData.indicator_chart_config,
                        indicatorKey
                      })
                    }
                    return (
                      <div
                        key={indicatorKey}
                        className="flex items-center gap-2 p-2 border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <span className="font-medium text-sm flex-1">{indicatorKey}</span>
                        <ChartTypePreview config={config} />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditingIndicatorKey(indicatorKey)
                            setChartConfigModalOpen(true)
                          }}
                        >
                          <Settings className="w-4 h-4 mr-2" />
                          설정
                        </Button>
                      </div>
                    )
                  })
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    표시할 지표가 없습니다.
                  </p>
                )}
              </div>
              <TradeChart chartData={chartData} />
              <ChartConfigModal
                open={chartConfigModalOpen}
                onOpenChange={setChartConfigModalOpen}
                field={editingIndicatorKey}
                config={chartData.indicator_chart_config?.[editingIndicatorKey] || null}
                onSave={(field, config) => {
                  setChartData({
                    ...chartData,
                    indicator_chart_config: {
                      ...(chartData.indicator_chart_config || {}),
                      [field]: config
                    }
                  })
                }}
              />
            </>
          ) : (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">차트 데이터를 불러올 수 없습니다</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Leg 상세 내역 */}
      <Card>
        <CardHeader>
          <CardTitle>청산 내역 (Legs)</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Leg</TableHead>
                <TableHead>청산 유형</TableHead>
                <TableHead>청산 시각</TableHead>
                <TableHead>청산가</TableHead>
                <TableHead>수량 비율</TableHead>
                <TableHead className="text-right">손익</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trade.legs.map((leg, idx) => (
                <TableRow key={leg.leg_id}>
                  <TableCell className="font-medium">
                    #{idx + 1}
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant="outline"
                      className={
                        leg.exit_type === 'TP1' ? 'border-blue-500 text-blue-500' :
                        leg.exit_type === 'SL' ? 'border-red-500 text-red-500' :
                        leg.exit_type === 'BE' ? 'border-yellow-500 text-yellow-500' :
                        'border-purple-500 text-purple-500'
                      }
                    >
                      {leg.exit_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatTimestamp(leg.exit_timestamp)}
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {formatPrice(leg.exit_price)}
                  </TableCell>
                  <TableCell>
                    {formatPercent(leg.qty_ratio * 100, 0)}
                  </TableCell>
                  <TableCell className={`text-right font-medium ${
                    leg.pnl >= 0 ? 'text-profit' : 'text-loss'
                  }`}>
                    {formatCurrency(leg.pnl)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          
          {/* 합계 */}
          <div className="mt-4 pt-4 border-t flex justify-between items-center">
            <span className="font-semibold">총 손익</span>
            <span className={`text-xl font-bold ${pnlColor}`}>
              {formatCurrency(trade.total_pnl || 0)}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

