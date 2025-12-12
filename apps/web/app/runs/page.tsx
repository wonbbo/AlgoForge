"use client"

import { useEffect, useState } from "react"
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Plus, PlayCircle, Eye } from "lucide-react"
import { runApi, datasetApi, strategyApi } from "@/lib/api-client"
import type { Run, Dataset, Strategy } from "@/lib/types"
import { formatTimestamp, getStatusColor } from "@/lib/utils"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

/**
 * Run 목록 페이지
 */
export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [creating, setCreating] = useState(false)

  // 폼 상태
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null)
  const [selectedStrategyId, setSelectedStrategyId] = useState<number | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [runsData, datasetsData, strategiesData] = await Promise.all([
        runApi.list(),
        datasetApi.list(),
        strategyApi.list(),
      ])
      setRuns(runsData)
      setDatasets(datasetsData)
      setStrategies(strategiesData)
    } catch (error: any) {
      console.error('Failed to load data:', error)
      toast.error('데이터를 불러오는데 실패했습니다', {
        description: error.message
      })
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedDatasetId || !selectedStrategyId) return

    setCreating(true)
    try {
      const createdRun = await runApi.create({
        dataset_id: selectedDatasetId,
        strategy_id: selectedStrategyId,
      })
      
      toast.success('Run이 생성되었습니다!', {
        description: `Run ID: ${createdRun.run_id} - 백테스트가 시작되었습니다.`
      })
      
      setShowCreateForm(false)
      setSelectedDatasetId(null)
      setSelectedStrategyId(null)
      await loadData()
    } catch (error: any) {
      console.error('Failed to create run:', error)
      toast.error('Run 생성에 실패했습니다', {
        description: error.message
      })
    } finally {
      setCreating(false)
    }
  }

  function getDatasetName(datasetId: number): string {
    return datasets.find(d => d.dataset_id === datasetId)?.name || `Dataset #${datasetId}`
  }

  function getStrategyName(strategyId: number): string {
    return strategies.find(s => s.strategy_id === strategyId)?.name || `Strategy #${strategyId}`
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Run</h1>
          <p className="text-muted-foreground">
            백테스트 실행 내역을 확인하세요
          </p>
        </div>
        <Button 
          onClick={() => setShowCreateForm(!showCreateForm)}
          disabled={datasets.length === 0 || strategies.length === 0}
        >
          <Plus className="mr-2 h-4 w-4" />
          Run 생성
        </Button>
      </div>

      {/* 안내 메시지 */}
      {(datasets.length === 0 || strategies.length === 0) && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <p className="text-sm text-yellow-800">
              Run을 생성하려면 먼저 데이터셋과 전략이 필요합니다.
              {datasets.length === 0 && " 데이터셋을 업로드하세요."}
              {strategies.length === 0 && " 전략을 생성하세요."}
            </p>
          </CardContent>
        </Card>
      )}

      {/* 생성 폼 */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>새 Run 생성</CardTitle>
            <CardDescription>
              데이터셋과 전략을 선택하여 백테스트를 실행하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="dataset">데이터셋</Label>
                <select
                  id="dataset"
                  value={selectedDatasetId || ""}
                  onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  required
                >
                  <option value="">데이터셋 선택</option>
                  {datasets.map((dataset) => (
                    <option key={dataset.dataset_id} value={dataset.dataset_id}>
                      {dataset.name} ({dataset.bars_count.toLocaleString()} 봉)
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="strategy">전략</Label>
                <select
                  id="strategy"
                  value={selectedStrategyId || ""}
                  onChange={(e) => setSelectedStrategyId(Number(e.target.value))}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  required
                >
                  <option value="">전략 선택</option>
                  {strategies.map((strategy) => (
                    <option key={strategy.strategy_id} value={strategy.strategy_id}>
                      {strategy.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCreateForm(false)}
                  disabled={creating}
                >
                  취소
                </Button>
                <Button 
                  type="submit" 
                  disabled={creating || !selectedDatasetId || !selectedStrategyId}
                >
                  {creating ? "생성 중..." : "실행"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Run 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>Run 목록</CardTitle>
          <CardDescription>총 {runs.length}개의 Run</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-8">
              로딩 중...
            </p>
          ) : runs.length === 0 ? (
            <div className="text-center py-12">
              <PlayCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">
                Run이 없습니다
              </p>
              {datasets.length > 0 && strategies.length > 0 && (
                <Button onClick={() => setShowCreateForm(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  첫 Run 생성
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run ID</TableHead>
                  <TableHead>데이터셋</TableHead>
                  <TableHead>전략</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead>생성일</TableHead>
                  <TableHead className="text-right">액션</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.run_id}>
                    <TableCell className="font-medium">
                      #{run.run_id}
                    </TableCell>
                    <TableCell className="text-sm">
                      {getDatasetName(run.dataset_id)}
                    </TableCell>
                    <TableCell className="text-sm">
                      {getStrategyName(run.strategy_id)}
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(run.status)}>
                        {run.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {run.started_at ? formatTimestamp(run.started_at) : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link href={`/runs/${run.run_id}`}>
                        <Button variant="ghost" size="icon">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

