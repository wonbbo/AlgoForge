"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, Upload, Trash2, FileText, Download } from "lucide-react"
import { datasetApi } from "@/lib/api-client"
import type { Dataset, BinanceFetchJob } from "@/lib/types"
import { formatDate } from "@/lib/utils"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const SUPPORTED_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]

/**
 * 데이터셋 관리 페이지
 */
export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [uploading, setUploading] = useState(false)

  // 공통 폼 상태 (이름/설명)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")

  // CSV 업로드 폼
  const [file, setFile] = useState<File | null>(null)

  // 바이낸스 수집 폼
  const [symbol, setSymbol] = useState("XRPUSDT")
  const [marketType, setMarketType] = useState<"spot" | "futures_um">("futures_um")
  const [timeframe, setTimeframe] = useState("5m")
  const [startDate, setStartDate] = useState("2024-01-01")
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10))

  // 바이낸스 Job 폴링 상태
  const [fetchJob, setFetchJob] = useState<BinanceFetchJob | null>(null)
  const pollTimerRef = useRef<number | null>(null)

  useEffect(() => {
    loadDatasets()
    return () => {
      if (pollTimerRef.current) window.clearInterval(pollTimerRef.current)
    }
  }, [])

  async function loadDatasets() {
    try {
      const data = await datasetApi.list()
      setDatasets(data)
    } catch (error) {
      console.error('Failed to load datasets:', error)
    } finally {
      setLoading(false)
    }
  }

  function resetCommonForm() {
    setName("")
    setDescription("")
    setFile(null)
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault()
    if (!file || !name) return

    setUploading(true)
    try {
      await datasetApi.create(file, name, description)
      setShowForm(false)
      resetCommonForm()
      await loadDatasets()
    } catch (error: any) {
      console.error('Failed to upload dataset:', error)
      let errorMessage = '데이터셋 업로드에 실패했습니다'
      if (error.message) errorMessage += ':\n' + error.message
      if (error.details) errorMessage += '\n\n상세: ' + JSON.stringify(error.details, null, 2)
      alert(errorMessage)
    } finally {
      setUploading(false)
    }
  }

  async function handleBinanceFetch(e: React.FormEvent) {
    e.preventDefault()
    if (!startDate || !endDate) return
    if (startDate > endDate) {
      alert("시작 날짜가 종료 날짜보다 늦습니다")
      return
    }

    setUploading(true)
    setFetchJob(null)
    try {
      const { job_id } = await datasetApi.fetchFromBinance({
        symbol,
        market_type: marketType,
        timeframe,
        start_date: startDate,
        end_date: endDate,
        name: name || undefined,
        description: description || undefined,
      })
      // 폴링 시작
      startPolling(job_id)
    } catch (error: any) {
      console.error('Failed to start Binance fetch:', error)
      alert('바이낸스 수집 시작 실패: ' + (error.message || '알 수 없는 오류'))
      setUploading(false)
    }
  }

  function startPolling(jobId: string) {
    if (pollTimerRef.current) window.clearInterval(pollTimerRef.current)
    pollTimerRef.current = window.setInterval(async () => {
      try {
        const job = await datasetApi.getFetchJob(jobId)
        setFetchJob(job)
        if (job.status === "COMPLETED" || job.status === "FAILED") {
          if (pollTimerRef.current) {
            window.clearInterval(pollTimerRef.current)
            pollTimerRef.current = null
          }
          setUploading(false)
          if (job.status === "COMPLETED") {
            await loadDatasets()
            // 3초 뒤 폼 닫고 상태 초기화
            setTimeout(() => {
              setShowForm(false)
              setFetchJob(null)
              resetCommonForm()
            }, 2000)
          }
        }
      } catch (error) {
        console.error('Poll failed:', error)
        if (pollTimerRef.current) {
          window.clearInterval(pollTimerRef.current)
          pollTimerRef.current = null
        }
        setUploading(false)
      }
    }, 1500)
  }

  async function handleDelete(id: number) {
    if (!confirm('정말로 삭제하시겠습니까?')) return

    try {
      await datasetApi.delete(id)
      await loadDatasets()
    } catch (error) {
      console.error('Failed to delete dataset:', error)
      alert('데이터셋 삭제에 실패했습니다')
    }
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">데이터셋</h1>
          <p className="text-muted-foreground">
            백테스트에 사용할 봉 데이터를 관리하세요
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="mr-2 h-4 w-4" />
          데이터셋 추가
        </Button>
      </div>

      {/* 생성 폼 */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>새 데이터셋</CardTitle>
            <CardDescription>CSV를 직접 업로드하거나 바이낸스에서 자동 수집합니다</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="binance" className="w-full">
              <TabsList className="grid w-full grid-cols-2 max-w-md">
                <TabsTrigger value="binance">
                  <Download className="mr-2 h-4 w-4" />
                  바이낸스 수집
                </TabsTrigger>
                <TabsTrigger value="csv">
                  <Upload className="mr-2 h-4 w-4" />
                  CSV 업로드
                </TabsTrigger>
              </TabsList>

              {/* 바이낸스 자동 수집 */}
              <TabsContent value="binance" className="mt-4">
                <form onSubmit={handleBinanceFetch} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="symbol">심볼</Label>
                      <Input
                        id="symbol"
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                        placeholder="XRPUSDT"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="market_type">시장</Label>
                      <Select value={marketType} onValueChange={(v) => setMarketType(v as any)}>
                        <SelectTrigger id="market_type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="futures_um">선물 (USDT-M)</SelectItem>
                          <SelectItem value="spot">현물 (Spot)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="timeframe">타임프레임</Label>
                      <Select value={timeframe} onValueChange={setTimeframe}>
                        <SelectTrigger id="timeframe">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {SUPPORTED_TIMEFRAMES.map((tf) => (
                            <SelectItem key={tf} value={tf}>{tf}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="start_date">시작 (UTC)</Label>
                      <Input
                        id="start_date"
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="end_date">종료 (UTC)</Label>
                      <Input
                        id="end_date"
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="b-name">이름 (선택)</Label>
                    <Input
                      id="b-name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="미지정 시 자동 생성 (예: XRPUSDT 2024 1h)"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="b-desc">설명 (선택)</Label>
                    <Input
                      id="b-desc"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                    />
                  </div>

                  {/* Job 진행 상태 */}
                  {fetchJob && (
                    <div className="rounded-md border p-3 text-sm space-y-1 bg-muted/50">
                      <div>
                        상태:{" "}
                        <span className={
                          fetchJob.status === "COMPLETED" ? "text-green-600 font-medium"
                            : fetchJob.status === "FAILED" ? "text-destructive font-medium"
                            : "text-blue-600 font-medium"
                        }>
                          {fetchJob.status}
                        </span>
                      </div>
                      {fetchJob.progress_message && (
                        <div className="text-muted-foreground">{fetchJob.progress_message}</div>
                      )}
                      {fetchJob.status === "COMPLETED" && fetchJob.bars_count != null && (
                        <div className="text-muted-foreground">
                          수집 완료: {fetchJob.bars_count.toLocaleString()}봉
                          {fetchJob.dataset_id != null && ` (dataset_id=${fetchJob.dataset_id})`}
                        </div>
                      )}
                      {fetchJob.error && (
                        <div className="text-destructive">오류: {fetchJob.error}</div>
                      )}
                    </div>
                  )}

                  <div className="flex justify-end space-x-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => { setShowForm(false); setFetchJob(null); resetCommonForm() }}
                      disabled={uploading}
                    >
                      취소
                    </Button>
                    <Button type="submit" disabled={uploading || !symbol || !startDate || !endDate}>
                      {uploading ? "수집 중..." : "수집 시작"}
                    </Button>
                  </div>
                </form>
              </TabsContent>

              {/* CSV 업로드 */}
              <TabsContent value="csv" className="mt-4">
                <form onSubmit={handleUpload} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="file">파일</Label>
                    <Input
                      id="file"
                      type="file"
                      accept=".csv"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      required
                    />
                    <p className="text-xs text-muted-foreground">
                      CSV 파일 형식: dt (YYYY-MM-DD HH:MM:SS), do, dh, dl, dc, dv, dd
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="u-name">이름</Label>
                    <Input
                      id="u-name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="예: BTC/USDT 2024 데이터"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="u-desc">설명 (선택)</Label>
                    <Input
                      id="u-desc"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="데이터셋에 대한 설명"
                    />
                  </div>

                  <div className="flex justify-end space-x-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => { setShowForm(false); resetCommonForm() }}
                      disabled={uploading}
                    >
                      취소
                    </Button>
                    <Button type="submit" disabled={uploading || !file || !name}>
                      {uploading ? "업로드 중..." : "업로드"}
                    </Button>
                  </div>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* 데이터셋 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>데이터셋 목록</CardTitle>
          <CardDescription>총 {datasets.length}개의 데이터셋</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-8">
              로딩 중...
            </p>
          ) : datasets.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">
                데이터셋이 없습니다
              </p>
              <Button onClick={() => setShowForm(true)}>
                <Download className="mr-2 h-4 w-4" />
                첫 데이터셋 추가
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>이름</TableHead>
                  <TableHead>심볼/시장</TableHead>
                  <TableHead>타임프레임</TableHead>
                  <TableHead>봉 수</TableHead>
                  <TableHead>기간</TableHead>
                  <TableHead>생성일</TableHead>
                  <TableHead className="text-right">액션</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {datasets.map((dataset) => (
                  <TableRow key={dataset.dataset_id}>
                    <TableCell className="font-medium">
                      {dataset.name}
                      {dataset.description && (
                        <p className="text-xs text-muted-foreground">
                          {dataset.description}
                        </p>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">
                      {dataset.symbol || "-"}
                      <br />
                      <span className="text-xs text-muted-foreground">
                        {dataset.market_type === "futures_um" ? "선물" : dataset.market_type === "spot" ? "현물" : "-"}
                      </span>
                    </TableCell>
                    <TableCell>{dataset.timeframe}</TableCell>
                    <TableCell>{dataset.bars_count.toLocaleString()}</TableCell>
                    <TableCell className="text-sm">
                      {formatDate(dataset.start_timestamp)}
                      <br />
                      ~ {formatDate(dataset.end_timestamp)}
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatDate(dataset.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(dataset.dataset_id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
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
