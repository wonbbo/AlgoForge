'use client'

import type { ChartSeriesConfig } from '@/lib/types'

interface ChartTypePreviewProps {
  config: ChartSeriesConfig | null
}

export function ChartTypePreview({ config }: ChartTypePreviewProps) {
  if (!config) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <div className="w-16 h-4 border border-dashed border-muted-foreground/30 rounded"></div>
        <span>미설정</span>
      </div>
    )
  }

  const color = config.properties?.color || '#2962FF'
  const lineWidth = config.properties?.lineWidth || 1
  const lineStyle = config.properties?.lineStyle !== undefined ? config.properties.lineStyle : 0

  return (
    <div className="flex items-center gap-2 text-xs">
      {/* 차트명 */}
      <span className="text-muted-foreground">{config.chart_name}</span>
      
      {/* 타입별 프리뷰 */}
      {config.type === 'line' && (
        <div className="flex items-center gap-1">
          <svg width="40" height="12" className="overflow-visible">
            {lineStyle === 0 ? (
              // 실선
              <line
                x1="0"
                y1="6"
                x2="40"
                y2="6"
                stroke={color}
                strokeWidth={lineWidth}
                strokeLinecap="round"
              />
            ) : lineStyle === 1 ? (
              // 점선
              <line
                x1="0"
                y1="6"
                x2="40"
                y2="6"
                stroke={color}
                strokeWidth={lineWidth}
                strokeDasharray="3 3"
                strokeLinecap="round"
              />
            ) : (
              // 긴 점선
              <line
                x1="0"
                y1="6"
                x2="40"
                y2="6"
                stroke={color}
                strokeWidth={lineWidth}
                strokeDasharray="5 3"
                strokeLinecap="round"
              />
            )}
          </svg>
          <span className="text-muted-foreground">Line</span>
        </div>
      )}
      
      {config.type === 'column' && (
        <div className="flex items-center gap-1">
          <div className="flex items-end gap-0.5 h-3">
            <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: color }}></div>
            <div className="w-2 h-3 rounded-sm" style={{ backgroundColor: color }}></div>
            <div className="w-2 h-2.5 rounded-sm" style={{ backgroundColor: color }}></div>
            <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: color }}></div>
          </div>
          <span className="text-muted-foreground">Column</span>
        </div>
      )}
      
      {config.type === 'point' && (
        <div className="flex items-center gap-1">
          <div className="flex items-center gap-0.5">
            <div 
              className="w-2 h-2 rounded-full" 
              style={{ backgroundColor: color }}
            ></div>
            <svg width="20" height="12" className="overflow-visible">
              <circle cx="10" cy="6" r="2" fill={color} />
            </svg>
            <div 
              className="w-2 h-2 rounded-full" 
              style={{ backgroundColor: color }}
            ></div>
          </div>
          <span className="text-muted-foreground">Point</span>
        </div>
      )}
    </div>
  )
}

