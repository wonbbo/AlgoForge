"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, GitBranch, Trash2, Wrench, Eye, Copy } from "lucide-react"
import { strategyApi } from "@/lib/api-client"
import type { Strategy } from "@/lib/types"
import { formatDate } from "@/lib/utils"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

/**
 * 전략 관리 페이지
 */
export default function StrategiesPage() {
  const router = useRouter()
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [creating, setCreating] = useState(false)

  // 폼 상태
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [definitionJson, setDefinitionJson] = useState("{}")

  useEffect(() => {
    loadStrategies()
  }, [])

  async function loadStrategies() {
    try {
      const data = await strategyApi.list()
      setStrategies(data)
    } catch (error: any) {
      console.error('Failed to load strategies:', error)
      toast.error('전략 목록을 불러오는데 실패했습니다', {
        description: error.message
      })
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!name) return

    // JSON 파싱 검증
    let definition: Record<string, any>
    try {
      definition = JSON.parse(definitionJson)
    } catch (error) {
      alert('유효하지 않은 JSON 형식입니다')
      return
    }

    setCreating(true)
    try {
      await strategyApi.create({
        name,
        description,
        definition,
      })
      toast.success('전략이 생성되었습니다!')
      setShowCreateForm(false)
      setName("")
      setDescription("")
      setDefinitionJson("{}")
      await loadStrategies()
    } catch (error: any) {
      console.error('Failed to create strategy:', error)
      toast.error('전략 생성에 실패했습니다', {
        description: error.message
      })
    } finally {
      setCreating(false)
    }
  }

  async function handleClone(strategy: Strategy) {
    try {
      // 전략을 복제하여 저장
      const clonedStrategy = await strategyApi.create({
        name: `${strategy.name} (복사본)`,
        description: strategy.description ? `${strategy.description} (복사본)` : '',
        definition: strategy.definition,
      })
      
      toast.success('전략이 복제되었습니다', {
        description: clonedStrategy.name
      })
      
      await loadStrategies()
    } catch (error: any) {
      console.error('Failed to clone strategy:', error)
      toast.error('전략 복제에 실패했습니다', {
        description: error.message
      })
    }
  }

  async function handleDelete(strategy: Strategy) {
    if (!confirm(`정말로 "${strategy.name}" 전략을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) return

    try {
      await strategyApi.delete(strategy.strategy_id)
      toast.success('전략이 삭제되었습니다')
      await loadStrategies()
    } catch (error: any) {
      console.error('Failed to delete strategy:', error)
      
      // 409 에러: Run이 존재하는 경우
      if (error.status === 409) {
        const detail = error.details || {}
        const runCount = detail.related_runs_count || '여러'
        const message = detail.message || `이 전략으로 생성된 Run이 ${runCount}개 존재합니다.`
        
        toast.error('전략을 삭제할 수 없습니다', {
          description: message,
          duration: 5000
        })
      } else {
        toast.error('전략 삭제에 실패했습니다', {
          description: error.message
        })
      }
    }
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">전략</h1>
          <p className="text-muted-foreground">
            백테스트할 거래 전략을 관리하세요
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push('/strategies/builder')}>
            <Wrench className="mr-2 h-4 w-4" />
            전략 빌더 (UI)
          </Button>
          <Button onClick={() => setShowCreateForm(!showCreateForm)}>
            <Plus className="mr-2 h-4 w-4" />
            전략 생성 (JSON)
          </Button>
        </div>
      </div>

      {/* 생성 폼 */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>새 전략 생성</CardTitle>
            <CardDescription>진입/청산 규칙을 정의하세요</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">이름</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="예: EMA Cross Strategy"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">설명 (선택)</Label>
                <Input
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="전략에 대한 설명"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="definition">전략 정의 (JSON)</Label>
                <textarea
                  id="definition"
                  value={definitionJson}
                  onChange={(e) => setDefinitionJson(e.target.value)}
                  className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                  placeholder='{\n  "entry_long": {"indicator": "ema_cross"},\n  "entry_short": {"indicator": "ema_cross_down"}\n}'
                  required
                />
                <p className="text-xs text-muted-foreground">
                  JSON 형식으로 전략 규칙을 정의하세요
                </p>
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
                <Button type="submit" disabled={creating || !name}>
                  {creating ? "생성 중..." : "생성"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* 전략 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>전략 목록</CardTitle>
          <CardDescription>총 {strategies.length}개의 전략</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-8">
              로딩 중...
            </p>
          ) : strategies.length === 0 ? (
            <div className="text-center py-12">
              <GitBranch className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">
                전략이 없습니다
              </p>
              <Button onClick={() => setShowCreateForm(true)}>
                <Plus className="mr-2 h-4 w-4" />
                첫 전략 생성
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>이름</TableHead>
                  <TableHead>설명</TableHead>
                  <TableHead>생성일</TableHead>
                  <TableHead className="text-right">액션</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {strategies.map((strategy) => (
                  <TableRow key={strategy.strategy_id}>
                    <TableCell className="font-medium">
                      {strategy.name}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {strategy.description || '-'}
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatDate(strategy.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => router.push(`/strategies/${strategy.strategy_id}`)}
                          title="상세 보기"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleClone(strategy)}
                          title="복제"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(strategy)}
                          title="삭제"
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
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

