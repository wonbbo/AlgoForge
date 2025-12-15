'use client'

/**
 * 지표 라이브러리 페이지
 * 
 * 내장 지표와 커스텀 지표 목록을 조회하고 관리합니다.
 */

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Plus, 
  TrendingUp, 
  Activity, 
  BarChart3, 
  Volume2,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { indicatorApi } from '@/lib/api-client'
import type { Indicator } from '@/lib/types'

export default function IndicatorsPage() {
  const [indicators, setIndicators] = useState<Indicator[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const fetchIndicators = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const params = filter === 'all' ? {} : { category: filter }
      const data = await indicatorApi.list(params)
      setIndicators(data)
    } catch (err: any) {
      console.error('지표 목록 조회 실패:', err)
      setError(err.message || '지표 목록을 불러오는데 실패했습니다')
    } finally {
      setIsLoading(false)
    }
  }, [filter])
  
  useEffect(() => {
    // 필터 변경 시 목록 재조회
    fetchIndicators()
  }, [fetchIndicators])
  
  const getCategoryIcon = (category: string) => {
    switch(category) {
      case 'trend': return TrendingUp
      case 'momentum': return Activity
      case 'volatility': return BarChart3
      case 'volume': return Volume2
      default: return Activity
    }
  }
  
  const getCategoryColor = (category: string) => {
    switch(category) {
      case 'trend': return 'text-blue-500'
      case 'momentum': return 'text-green-500'
      case 'volatility': return 'text-orange-500'
      case 'volume': return 'text-purple-500'
      default: return 'text-gray-500'
    }
  }
  
  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">지표 라이브러리</h1>
          <p className="text-muted-foreground mt-1">
            내장 지표와 커스텀 지표를 관리합니다
          </p>
        </div>
        <Link href="/indicators/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            커스텀 지표 추가
          </Button>
        </Link>
      </div>
      
      {/* 카테고리 필터 */}
      <div className="flex gap-2 mb-6">
        {[
          { value: 'all', label: '전체' },
          { value: 'trend', label: 'Trend' },
          { value: 'momentum', label: 'Momentum' },
          { value: 'volatility', label: 'Volatility' },
          { value: 'volume', label: 'Volume' }
        ].map(cat => (
          <Button
            key={cat.value}
            variant={filter === cat.value ? 'default' : 'outline'}
            onClick={() => setFilter(cat.value)}
          >
            {cat.label}
          </Button>
        ))}
      </div>
      
      {/* 로딩 상태 */}
      {isLoading && (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      )}
      
      {/* 에러 상태 */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive rounded-lg">
          <AlertCircle className="w-5 h-5" />
          <p>{error}</p>
          <Button variant="outline" size="sm" onClick={fetchIndicators} className="ml-auto">
            다시 시도
          </Button>
        </div>
      )}
      
      {/* 지표 목록 */}
      {!isLoading && !error && (
        <>
          {indicators.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">지표가 없습니다</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {indicators.map(indicator => {
                const Icon = getCategoryIcon(indicator.category)
                const colorClass = getCategoryColor(indicator.category)
                
                return (
                  <Link 
                    key={indicator.indicator_id} 
                    href={`/indicators/${indicator.type}`}
                  >
                    <Card className="p-4 hover:shadow-lg transition-all hover:border-primary cursor-pointer h-full">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Icon className={`w-5 h-5 ${colorClass}`} />
                          <h3 className="font-bold text-lg">{indicator.name}</h3>
                        </div>
                        <Badge 
                          variant={indicator.implementation_type === 'builtin' ? 'default' : 'secondary'}
                        >
                          {indicator.implementation_type === 'builtin' ? '내장' : '커스텀'}
                        </Badge>
                      </div>
                      
                      <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                        {indicator.description || '설명 없음'}
                      </p>
                      
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="outline" className="text-xs">
                          {indicator.category}
                        </Badge>
                        {indicator.output_fields.map(field => (
                          <Badge key={field} variant="outline" className="text-xs">
                            출력: {field}
                          </Badge>
                        ))}
                        {indicator.output_fields.length > 1 && (
                          <Badge variant="outline" className="text-xs font-semibold">
                            {indicator.output_fields.length}개 출력
                          </Badge>
                        )}
                      </div>
                    </Card>
                  </Link>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}

