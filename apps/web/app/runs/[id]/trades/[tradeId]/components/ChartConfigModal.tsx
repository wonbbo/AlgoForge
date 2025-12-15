'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { ChartSeriesConfig } from '@/lib/types'

interface ChartConfigModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  field: string
  config: ChartSeriesConfig | null
  onSave: (field: string, config: ChartSeriesConfig) => void
}

export function ChartConfigModal({
  open,
  onOpenChange,
  field,
  config,
  onSave
}: ChartConfigModalProps) {
  const [localConfig, setLocalConfig] = useState<ChartSeriesConfig>({
    chart_name: 'main',
    type: 'line',
    properties: {
      color: '#2962FF',
      lineWidth: 1,
      lineStyle: 0,
      visible: true
    }
  })

  useEffect(() => {
    if (config) {
      // 포인트 타입인 경우 chart_name을 강제로 main으로 설정
      const updatedConfig = {
        ...config,
        chart_name: config.type === 'point' ? 'main' : config.chart_name
      }
      setLocalConfig(updatedConfig)
    } else {
      setLocalConfig({
        chart_name: 'main',
        type: 'line',
        properties: {
          color: '#2962FF',
          lineWidth: 1,
          lineStyle: 0,
          visible: true
        }
      })
    }
  }, [config, open])
  
  // 타입이 point로 변경되면 chart_name을 main으로 강제 설정
  useEffect(() => {
    if (localConfig.type === 'point' && localConfig.chart_name !== 'main') {
      setLocalConfig(prev => ({
        ...prev,
        chart_name: 'main'
      }))
    }
  }, [localConfig.type, localConfig.chart_name])

  const handleSave = () => {
    onSave(field, localConfig)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{field} 차트 설정</DialogTitle>
          <DialogDescription>
            차트에 표시될 {field} 지표의 시각화 설정을 구성합니다.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div>
            <Label htmlFor="chart_name">차트명</Label>
            <Input
              id="chart_name"
              value={localConfig.chart_name}
              onChange={e => setLocalConfig({
                ...localConfig,
                chart_name: e.target.value
              })}
              placeholder="main"
              disabled={localConfig.type === 'point'}
              className={localConfig.type === 'point' ? 'bg-muted cursor-not-allowed' : ''}
            />
            {localConfig.type === 'point' && (
              <p className="text-xs text-muted-foreground mt-1">
                포인트 타입은 항상 main 차트에만 표시됩니다.
              </p>
            )}
          </div>
          
          <div>
            <Label htmlFor="type">타입</Label>
            <select
              id="type"
              value={localConfig.type}
              onChange={e => setLocalConfig({
                ...localConfig,
                type: e.target.value as 'line' | 'column' | 'point'
              })}
              className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm"
            >
              <option value="line">Line</option>
              <option value="column">Column</option>
              <option value="point">Point</option>
            </select>
          </div>
          
          <div>
            <Label htmlFor="color">색상</Label>
            <Input
              id="color"
              type="color"
              value={localConfig.properties?.color || '#2962FF'}
              onChange={e => setLocalConfig({
                ...localConfig,
                properties: {
                  ...localConfig.properties,
                  color: e.target.value
                }
              })}
              className="h-10"
            />
          </div>
          
          {localConfig.type === 'line' && (
            <>
              <div>
                <Label htmlFor="lineWidth">굵기</Label>
                <Input
                  id="lineWidth"
                  type="number"
                  min="1"
                  max="10"
                  value={localConfig.properties?.lineWidth || 1}
                  onChange={e => setLocalConfig({
                    ...localConfig,
                    properties: {
                      ...localConfig.properties,
                      lineWidth: parseInt(e.target.value) || 1
                    }
                  })}
                />
              </div>
              
              <div>
                <Label htmlFor="lineStyle">라인 종류</Label>
                <select
                  id="lineStyle"
                  value={localConfig.properties?.lineStyle !== undefined ? localConfig.properties.lineStyle : 0}
                  onChange={e => setLocalConfig({
                    ...localConfig,
                    properties: {
                      ...localConfig.properties,
                      lineStyle: parseInt(e.target.value)
                    }
                  })}
                  className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm"
                >
                  <option value="0">실선</option>
                  <option value="1">점선</option>
                  <option value="2">점선 (긴 간격)</option>
                </select>
              </div>
            </>
          )}
          
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="visible"
              checked={localConfig.properties?.visible !== false}
              onChange={e => setLocalConfig({
                ...localConfig,
                properties: {
                  ...localConfig.properties,
                  visible: e.target.checked
                }
              })}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="visible" className="text-sm font-normal cursor-pointer">
              표시 여부
            </Label>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            취소
          </Button>
          <Button onClick={handleSave}>
            저장
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

