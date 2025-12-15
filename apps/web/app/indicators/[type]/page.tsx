'use client'

/**
 * 지표 상세/수정 페이지
 * 
 * 지표 정보를 확인하고, 커스텀 지표인 경우 수정/삭제할 수 있습니다.
 */

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { 
  ArrowLeft,
  Edit,
  Trash2,
  Save,
  X,
  Loader2,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Activity,
  BarChart3,
  Volume2
} from 'lucide-react'
import { indicatorApi } from '@/lib/api-client'
import type { Indicator, IndicatorUpdate, CodeValidationResult } from '@/lib/types'

export default function IndicatorDetailPage() {
  const router = useRouter()
  const params = useParams()
  const indicatorType = params.type as string
  
  const [indicator, setIndicator] = useState<Indicator | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // 수정 모드
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState<IndicatorUpdate>({})
  const [validationResult, setValidationResult] = useState<CodeValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  
  useEffect(() => {
    fetchIndicator()
  }, [indicatorType])
  
  const fetchIndicator = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const data = await indicatorApi.get(indicatorType)
      setIndicator(data)
      
      // 수정 데이터 초기화
      if (data.implementation_type === 'custom') {
        setEditData({
          name: data.name,
          description: data.description,
          category: data.category,
          code: data.code,  // 코드 포함
          params_schema: data.params_schema,
          output_fields: data.output_fields,
        })
      }
    } catch (err: any) {
      console.error('지표 조회 실패:', err)
      setError(err.message || '지표를 불러오는데 실패했습니다')
    } finally {
      setIsLoading(false)
    }
  }
  
  const getCategoryIcon = (category: string) => {
    switch(category) {
      case 'trend': return TrendingUp
      case 'momentum': return Activity
      case 'volatility': return BarChart3
      case 'volume': return Volume2
      default: return Activity
    }
  }
  
  // 코드 검증
  const handleValidate = async () => {
    if (!editData.code?.trim()) {
      setValidationResult({
        is_valid: false,
        message: '코드를 입력해주세요',
        errors: ['코드가 비어있습니다']
      })
      return
    }
    
    setIsValidating(true)
    setValidationResult(null)
    
    try {
      const result = await indicatorApi.validateCode(editData.code)
      setValidationResult(result)
    } catch (err: any) {
      setValidationResult({
        is_valid: false,
        message: '검증 실패',
        errors: [err.message]
      })
    } finally {
      setIsValidating(false)
    }
  }
  
  // 수정 저장
  const handleSave = async () => {
    // 코드를 수정한 경우 검증 필요
    if (editData.code && !validationResult?.is_valid) {
      alert('코드 수정 시 검증을 통과해야 합니다')
      return
    }
    
    // params_schema JSON 검증
    if (editData.params_schema) {
      try {
        JSON.parse(editData.params_schema)
      } catch (err) {
        alert('파라미터 스키마가 올바른 JSON 형식이 아닙니다')
        return
      }
    }
    
    // output_fields 검증
    if (editData.output_fields && editData.output_fields.length === 0) {
      alert('최소 하나의 출력 필드가 필요합니다')
      return
    }
    
    setIsSaving(true)
    
    try {
      const updated = await indicatorApi.update(indicatorType, editData)
      setIndicator(updated)
      setIsEditing(false)
      setEditData({})
      setValidationResult(null)
    } catch (err: any) {
      alert(`수정 실패: ${err.message}`)
    } finally {
      setIsSaving(false)
    }
  }
  
  // 삭제
  const handleDelete = async () => {
    if (!confirm(`'${indicator?.name}' 지표를 삭제하시겠습니까?`)) {
      return
    }
    
    try {
      await indicatorApi.delete(indicatorType)
      router.push('/indicators')
    } catch (err: any) {
      alert(`삭제 실패: ${err.message}`)
    }
  }
  
  if (isLoading) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <div className="flex justify-center items-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }
  
  if (error || !indicator) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive rounded-lg">
          <AlertCircle className="w-5 h-5" />
          <p>{error || '지표를 찾을 수 없습니다'}</p>
          <Button variant="outline" size="sm" onClick={() => router.back()} className="ml-auto">
            뒤로
          </Button>
        </div>
      </div>
    )
  }
  
  const Icon = getCategoryIcon(indicator.category)
  const isBuiltin = indicator.implementation_type === 'builtin'
  
  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.back()}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            뒤로
          </Button>
          <div className="flex items-center gap-3">
            <Icon className="w-8 h-8" />
            <div>
              <h1 className="text-3xl font-bold">{indicator.name}</h1>
              <p className="text-muted-foreground">{indicator.type}</p>
            </div>
          </div>
        </div>
        
        {!isBuiltin && (
          <div className="flex gap-2">
            {!isEditing ? (
              <>
                <Button variant="outline" onClick={() => setIsEditing(true)}>
                  <Edit className="w-4 h-4 mr-2" />
                  수정
                </Button>
                <Button variant="destructive" onClick={handleDelete}>
                  <Trash2 className="w-4 h-4 mr-2" />
                  삭제
                </Button>
              </>
            ) : (
              <>
                <Button variant="outline" onClick={() => {
                  setIsEditing(false)
                  setEditData({})
                  setValidationResult(null)
                }}>
                  <X className="w-4 h-4 mr-2" />
                  취소
                </Button>
                <Button onClick={handleSave} disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      저장 중...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      저장
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        )}
      </div>
      
      {/* 기본 정보 */}
      <Card className="p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">기본 정보</h2>
        
        <div className="space-y-4">
          {isEditing ? (
            <>
              <div>
                <Label>지표 이름</Label>
                <Input
                  value={editData.name}
                  onChange={e => setEditData({...editData, name: e.target.value})}
                />
              </div>
              <div>
                <Label>설명</Label>
                <Textarea
                  value={editData.description}
                  onChange={e => setEditData({...editData, description: e.target.value})}
                  rows={2}
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <Label>설명</Label>
                <p className="text-sm mt-1">{indicator.description || '설명 없음'}</p>
              </div>
            </>
          )}
          
          <div className="flex gap-4">
            <div className="flex-1">
              <Label>카테고리</Label>
              {isEditing ? (
                <select
                  value={editData.category || indicator.category}
                  onChange={e => setEditData({...editData, category: e.target.value as any})}
                  className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm mt-1"
                >
                  <option value="trend">Trend (추세)</option>
                  <option value="momentum">Momentum (모멘텀)</option>
                  <option value="volatility">Volatility (변동성)</option>
                  <option value="volume">Volume (거래량)</option>
                </select>
              ) : (
                <p className="text-sm mt-1">
                  <Badge variant="outline">{indicator.category}</Badge>
                </p>
              )}
            </div>
            <div className="flex-1">
              <Label>타입</Label>
              <p className="text-sm mt-1">
                <Badge variant={isBuiltin ? 'default' : 'secondary'}>
                  {isBuiltin ? '내장' : '커스텀'}
                </Badge>
              </p>
            </div>
          </div>
          
          {isEditing ? (
            <>
              <div>
                <Label>출력 필드</Label>
                <Input
                  value={editData.output_fields?.join(', ') || ''}
                  onChange={e => {
                    const fields = e.target.value.split(',').map(f => f.trim()).filter(f => f)
                    setEditData({...editData, output_fields: fields})
                  }}
                  placeholder="main, signal, histogram (쉼표로 구분)"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  쉼표(,)로 구분하여 입력하세요. 예: main, signal, histogram
                </p>
              </div>
              
              <div>
                <Label>파라미터 스키마</Label>
                <Textarea
                  value={editData.params_schema || ''}
                  onChange={e => setEditData({...editData, params_schema: e.target.value})}
                  rows={4}
                  className="font-mono text-sm"
                  placeholder='{"period": 20, "source": "close"}'
                />
                <p className="text-xs text-muted-foreground mt-1">
                  JSON 형식으로 입력하세요. 기본 파라미터 값을 포함해야 합니다.
                </p>
              </div>
            </>
          ) : (
            <>
              <div>
                <Label>출력 필드</Label>
                <div className="flex gap-2 mt-1">
                  {indicator.output_fields.map(field => (
                    <Badge key={field} variant="outline">{field}</Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <Label>파라미터 스키마</Label>
                <pre className="text-sm mt-1 p-3 bg-muted rounded-md overflow-x-auto font-mono">
                  {indicator.params_schema || '{}'}
                </pre>
              </div>
            </>
          )}
        </div>
      </Card>
      
      {/* 코드 (커스텀 지표만) */}
      {!isBuiltin && (
        <Card className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Python 코드</h2>
            {isEditing && editData.code && (
              <Button 
                variant="outline" 
                size="sm"
                onClick={handleValidate}
                disabled={isValidating}
              >
                {isValidating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    검증 중...
                  </>
                ) : (
                  '코드 검증'
                )}
              </Button>
            )}
          </div>
          
          {isEditing ? (
            <>
              <Textarea
                value={editData.code || ''}
                onChange={e => setEditData({...editData, code: e.target.value})}
                rows={20}
                className="font-mono text-sm"
              />
              
              {validationResult && (
                <div className={`mt-4 p-4 rounded-lg flex items-start gap-3 ${
                  validationResult.is_valid 
                    ? 'bg-green-50 dark:bg-green-950 text-green-800 dark:text-green-200' 
                    : 'bg-red-50 dark:bg-red-950 text-red-800 dark:text-red-200'
                }`}>
                  {validationResult.is_valid ? (
                    <CheckCircle className="w-5 h-5 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className="font-bold">{validationResult.message}</p>
                    {validationResult.errors && (
                      <ul className="mt-2 space-y-1">
                        {validationResult.errors.map((err, i) => (
                          <li key={i} className="text-sm">• {err}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <pre className="text-sm p-4 bg-muted rounded-md overflow-x-auto font-mono">
              {indicator.code || '// 코드 없음'}
            </pre>
          )}
        </Card>
      )}
    </div>
  )
}

