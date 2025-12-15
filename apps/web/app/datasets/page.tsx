"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, Upload, Trash2, FileText } from "lucide-react"
import { datasetApi } from "@/lib/api-client"
import type { Dataset } from "@/lib/types"
import { formatTimestamp, formatDate } from "@/lib/utils"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

/**
 * 데이터셋 관리 페이지
 */
export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [uploading, setUploading] = useState(false)

  // 폼 상태
  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")

  useEffect(() => {
    loadDatasets()
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

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault()
    if (!file || !name) return

    setUploading(true)
    try {
      await datasetApi.create(file, name, description)
      setShowUploadForm(false)
      setFile(null)
      setName("")
      setDescription("")
      await loadDatasets()
    } catch (error: any) {
      console.error('Failed to upload dataset:', error)
      
      // 에러 메시지를 더 자세하게 표시
      let errorMessage = '데이터셋 업로드에 실패했습니다'
      if (error.message) {
        errorMessage += ':\n' + error.message
      }
      if (error.details) {
        errorMessage += '\n\n상세: ' + JSON.stringify(error.details, null, 2)
      }
      
      alert(errorMessage)
    } finally {
      setUploading(false)
    }
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
        <Button onClick={() => setShowUploadForm(!showUploadForm)}>
          <Plus className="mr-2 h-4 w-4" />
          데이터셋 업로드
        </Button>
      </div>

      {/* 업로드 폼 */}
      {showUploadForm && (
        <Card>
          <CardHeader>
            <CardTitle>새 데이터셋 업로드</CardTitle>
            <CardDescription>CSV 형식의 봉 데이터를 업로드하세요</CardDescription>
          </CardHeader>
          <CardContent>
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
                <Label htmlFor="name">이름</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="예: BTC/USDT 2024 데이터"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">설명 (선택)</Label>
                <Input
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="데이터셋에 대한 설명"
                />
              </div>

              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowUploadForm(false)}
                  disabled={uploading}
                >
                  취소
                </Button>
                <Button type="submit" disabled={uploading || !file || !name}>
                  {uploading ? "업로드 중..." : "업로드"}
                </Button>
              </div>
            </form>
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
              <Button onClick={() => setShowUploadForm(true)}>
                <Upload className="mr-2 h-4 w-4" />
                첫 데이터셋 업로드
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>이름</TableHead>
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

