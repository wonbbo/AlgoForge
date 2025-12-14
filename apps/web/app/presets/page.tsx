"use client"

import { useEffect, useState } from "react"
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Plus, Edit, Trash2, RefreshCw, Star, StarOff } from "lucide-react"
import { presetApi } from "@/lib/api-client"
import type { Preset, PresetCreate, PresetUpdate } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

/**
 * 프리셋 관리 페이지
 */
export default function PresetsPage() {
  const [presets, setPresets] = useState<Preset[]>([])
  const [loading, setLoading] = useState(true)
  const [showDialog, setShowDialog] = useState(false)
  const [editingPreset, setEditingPreset] = useState<Preset | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // 폼 상태
  const [formData, setFormData] = useState<PresetCreate>({
    name: "",
    description: "",
    initial_balance: 1000,
    risk_percent: 0.02,
    risk_reward_ratio: 1.5,
    rebalance_interval: 50,
  })

  useEffect(() => {
    loadPresets()
  }, [])

  async function loadPresets() {
    setLoading(true)
    try {
      const data = await presetApi.list()
      setPresets(data)
    } catch (error: any) {
      console.error('Failed to load presets:', error)
      toast.error('프리셋 목록을 불러오는데 실패했습니다', {
        description: error.message
      })
    } finally {
      setLoading(false)
    }
  }

  function openCreateDialog() {
    setEditingPreset(null)
    setFormData({
      name: "",
      description: "",
      initial_balance: 1000,
      risk_percent: 0.02,
      risk_reward_ratio: 1.5,
      rebalance_interval: 50,
    })
    setShowDialog(true)
  }

  function openEditDialog(preset: Preset) {
    setEditingPreset(preset)
    setFormData({
      name: preset.name,
      description: preset.description || "",
      initial_balance: preset.initial_balance,
      risk_percent: preset.risk_percent,
      risk_reward_ratio: preset.risk_reward_ratio,
      rebalance_interval: preset.rebalance_interval,
    })
    setShowDialog(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    
    // 유효성 검증
    if (formData.risk_percent <= 0 || formData.risk_percent > 1) {
      toast.error('리스크 비율은 0 초과 1 이하여야 합니다')
      return
    }
    
    if (formData.risk_reward_ratio <= 0) {
      toast.error('리스크 보상 비율은 0보다 커야 합니다')
      return
    }
    
    if (formData.rebalance_interval < 1) {
      toast.error('재평가 주기는 1 이상이어야 합니다')
      return
    }

    setSubmitting(true)
    try {
      if (editingPreset) {
        // 수정
        await presetApi.update(editingPreset.preset_id, formData)
        toast.success('프리셋이 수정되었습니다')
      } else {
        // 생성
        await presetApi.create(formData)
        toast.success('프리셋이 생성되었습니다')
      }
      
      setShowDialog(false)
      await loadPresets()
    } catch (error: any) {
      console.error('Failed to save preset:', error)
      toast.error(editingPreset ? '프리셋 수정에 실패했습니다' : '프리셋 생성에 실패했습니다', {
        description: error.message
      })
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(preset: Preset) {
    if (preset.is_default) {
      toast.error('기본 프리셋은 삭제할 수 없습니다')
      return
    }

    if (!confirm(`프리셋 "${preset.name}"을(를) 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) {
      return
    }

    try {
      await presetApi.delete(preset.preset_id)
      toast.success('프리셋이 삭제되었습니다')
      await loadPresets()
    } catch (error: any) {
      console.error('Failed to delete preset:', error)
      toast.error('프리셋 삭제에 실패했습니다', {
        description: error.message
      })
    }
  }

  async function handleSetDefault(preset: Preset) {
    if (preset.is_default) {
      return
    }

    try {
      await presetApi.setDefault(preset.preset_id)
      toast.success(`"${preset.name}"을(를) 기본 프리셋으로 설정했습니다`)
      await loadPresets()
    } catch (error: any) {
      console.error('Failed to set default preset:', error)
      toast.error('기본 프리셋 설정에 실패했습니다', {
        description: error.message
      })
    }
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">설정 프리셋</h1>
          <p className="text-muted-foreground">
            Run 수행 시 사용되는 리스크 관리 설정을 관리합니다
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline"
            onClick={loadPresets}
            disabled={loading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
          <Button onClick={openCreateDialog}>
            <Plus className="mr-2 h-4 w-4" />
            프리셋 생성
          </Button>
        </div>
      </div>

      {/* 프리셋 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>프리셋 목록</CardTitle>
          <CardDescription>총 {presets.length}개의 프리셋</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-8">
              로딩 중...
            </p>
          ) : presets.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground mb-4">
                프리셋이 없습니다
              </p>
              <Button onClick={openCreateDialog}>
                <Plus className="mr-2 h-4 w-4" />
                첫 프리셋 생성
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>이름</TableHead>
                  <TableHead>설명</TableHead>
                  <TableHead className="text-right">초기 자산</TableHead>
                  <TableHead className="text-right">리스크 %</TableHead>
                  <TableHead className="text-right">R:R</TableHead>
                  <TableHead className="text-right">재평가 주기</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead className="text-right">액션</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {presets.map((preset) => (
                  <TableRow key={preset.preset_id}>
                    <TableCell className="font-medium">
                      {preset.name}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
                      {preset.description || '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {preset.initial_balance.toLocaleString()} USDT
                    </TableCell>
                    <TableCell className="text-right">
                      {(preset.risk_percent * 100).toFixed(2)}%
                    </TableCell>
                    <TableCell className="text-right">
                      {preset.risk_reward_ratio}
                    </TableCell>
                    <TableCell className="text-right">
                      {preset.rebalance_interval} 거래
                    </TableCell>
                    <TableCell>
                      {preset.is_default && (
                        <Badge variant="default">기본</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {!preset.is_default && (
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleSetDefault(preset)}
                            title="기본으로 설정"
                          >
                            <StarOff className="h-4 w-4" />
                          </Button>
                        )}
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => openEditDialog(preset)}
                          title="수정"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => handleDelete(preset)}
                          disabled={preset.is_default}
                          title={preset.is_default ? "기본 프리셋은 삭제할 수 없습니다" : "삭제"}
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

      {/* 생성/수정 다이얼로그 */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>
                {editingPreset ? '프리셋 수정' : '새 프리셋 생성'}
              </DialogTitle>
              <DialogDescription>
                Run 수행 시 사용될 리스크 관리 설정을 입력하세요
              </DialogDescription>
            </DialogHeader>
            
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">이름 *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="예: 공격적, 보수적"
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="description">설명</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="프리셋에 대한 설명을 입력하세요"
                  rows={2}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="initial_balance">초기 자산 (USDT) *</Label>
                <Input
                  id="initial_balance"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.initial_balance}
                  onChange={(e) => setFormData({ ...formData, initial_balance: parseFloat(e.target.value) })}
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="risk_percent">리스크 비율 (%) *</Label>
                <Input
                  id="risk_percent"
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="100"
                  value={(formData.risk_percent * 100).toFixed(2)}
                  onChange={(e) => setFormData({ ...formData, risk_percent: parseFloat(e.target.value) / 100 })}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  거래당 최대 손실 비율 (예: 2% = 0.02)
                </p>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="risk_reward_ratio">리스크 보상 비율 (R:R) *</Label>
                <Input
                  id="risk_reward_ratio"
                  type="number"
                  step="0.1"
                  min="0.1"
                  value={formData.risk_reward_ratio}
                  onChange={(e) => setFormData({ ...formData, risk_reward_ratio: parseFloat(e.target.value) })}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  리스크 대비 보상 비율 (예: 1.5 = 1:1.5)
                </p>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="rebalance_interval">재평가 주기 (거래 단위) *</Label>
                <Input
                  id="rebalance_interval"
                  type="number"
                  step="1"
                  min="1"
                  value={formData.rebalance_interval}
                  onChange={(e) => setFormData({ ...formData, rebalance_interval: parseInt(e.target.value) })}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  몇 거래마다 잔고를 재평가할지 설정 (예: 50)
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
                disabled={submitting}
              >
                취소
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "저장 중..." : editingPreset ? "수정" : "생성"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
