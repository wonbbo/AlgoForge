'use client'

/**
 * 커스텀 지표 등록 페이지
 * 
 * 사용자가 Python 코드로 커스텀 지표를 작성하고 등록합니다.
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { 
  AlertCircle, 
  CheckCircle, 
  Loader2,
  ArrowLeft,
  Code
} from 'lucide-react'
import { indicatorApi } from '@/lib/api-client'
import type { IndicatorCreate, CodeValidationResult } from '@/lib/types'

export default function NewIndicatorPage() {
  const router = useRouter()
  
  const [formData, setFormData] = useState<IndicatorCreate>({
    name: '',
    type: '',
    description: '',
    category: 'trend',
    code: `def calculate_custom_indicator(df, params):
    """
    커스텀 지표 계산 함수
    
    Args:
        df: OHLCV DataFrame (columns: timestamp, open, high, low, close, volume, direction)
        params: 파라미터 딕셔너리
    
    Returns:
        pd.Series 또는 Dict[str, pd.Series]:
        - 단일 값: pd.Series 반환 (예: df['close'].rolling(window=period).mean())
        - 여러 값: Dict[str, pd.Series] 반환 (예: {'main': ..., 'signal': ..., 'histogram': ...})
        
    중요: output_fields에 여러 필드가 있는 경우 반드시 Dict[str, pd.Series] 형태로 반환해야 합니다.
    """
    import pandas as pd
    
    period = params.get('period', 20)
    
    # 예시 1: 단일 값 반환 (output_fields: ['main'])
    # return df['close'].rolling(window=period).mean().fillna(0)
    
    # 예시 2: 여러 값 반환 (output_fields: ['main', 'signal', 'histogram'])
    sma = df['close'].rolling(window=period).mean()
    signal = sma.rolling(window=9).mean()
    histogram = sma - signal
    
    return {
        'main': sma.fillna(0),
        'signal': signal.fillna(0),
        'histogram': histogram.fillna(0)
    }`,
    params_schema: '{"period": 20}',
    output_fields: ['main']
  })
  
  const [outputFieldsInput, setOutputFieldsInput] = useState('main')
  const [validationResult, setValidationResult] = useState<CodeValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // 코드 검증
  const handleValidate = async () => {
    if (!formData.code.trim()) {
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
      const result = await indicatorApi.validateCode(formData.code)
      setValidationResult(result)
    } catch (err: any) {
      setValidationResult({
        is_valid: false,
        message: '검증 실패',
        errors: [err.message || '서버와의 통신에 실패했습니다']
      })
    } finally {
      setIsValidating(false)
    }
  }
  
  // 폼 제출
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // 검증 확인
    if (!validationResult?.is_valid) {
      alert('먼저 코드 검증을 통과해야 합니다')
      return
    }
    
    // output_fields 파싱
    const outputFields = outputFieldsInput
      .split(',')
      .map(f => f.trim())
      .filter(f => f.length > 0)
    
    if (outputFields.length === 0) {
      alert('최소 하나의 출력 필드가 필요합니다')
      return
    }
    
    // params_schema JSON 검증
    try {
      JSON.parse(formData.params_schema)
    } catch {
      alert('파라미터 스키마는 유효한 JSON이어야 합니다')
      return
    }
    
    setIsSubmitting(true)
    setError(null)
    
    try {
      await indicatorApi.create({
        ...formData,
        output_fields: outputFields
      })
      
      // 성공 시 목록 페이지로 이동
      router.push('/indicators')
    } catch (err: any) {
      console.error('지표 등록 실패:', err)
      setError(err.message || '지표 등록에 실패했습니다')
      setIsSubmitting(false)
    }
  }
  
  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* 헤더 */}
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.back()}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          뒤로
        </Button>
        <div>
          <h1 className="text-3xl font-bold">커스텀 지표 등록</h1>
          <p className="text-muted-foreground mt-1">
            Python 코드로 나만의 지표를 만드세요
          </p>
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 기본 정보 */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Code className="w-5 h-5" />
            기본 정보
          </h2>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">지표 이름 *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  placeholder="예: Custom MACD"
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="type">지표 타입 (고유 ID) *</Label>
                <Input
                  id="type"
                  value={formData.type}
                  onChange={e => setFormData({...formData, type: e.target.value})}
                  placeholder="예: custom_macd"
                  pattern="[a-z_][a-z0-9_]*"
                  title="소문자, 숫자, 언더스코어만 사용 가능 (숫자로 시작 불가)"
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">
                  소문자, 숫자, 언더스코어만 사용
                </p>
              </div>
            </div>
            
            <div>
              <Label htmlFor="description">설명</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={e => setFormData({...formData, description: e.target.value})}
                placeholder="지표에 대한 설명을 입력하세요"
                rows={2}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="category">카테고리 *</Label>
                <select
                  id="category"
                  value={formData.category}
                  onChange={e => setFormData({...formData, category: e.target.value as any})}
                  className="w-full border rounded-md p-2 bg-background"
                  required
                >
                  <option value="trend">Trend (추세)</option>
                  <option value="momentum">Momentum (모멘텀)</option>
                  <option value="volatility">Volatility (변동성)</option>
                  <option value="volume">Volume (거래량)</option>
                </select>
              </div>
              
              <div>
                <Label htmlFor="output_fields">출력 필드 *</Label>
                <Input
                  id="output_fields"
                  value={outputFieldsInput}
                  onChange={e => setOutputFieldsInput(e.target.value)}
                  placeholder="예: main 또는 main,signal,histogram"
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">
                쉼표로 구분 (단일 출력은 &apos;main&apos;)
                </p>
              </div>
            </div>
            
            <div>
              <Label htmlFor="params_schema">파라미터 스키마 (JSON) *</Label>
              <Textarea
                id="params_schema"
                value={formData.params_schema}
                onChange={e => setFormData({...formData, params_schema: e.target.value})}
                placeholder='{"period": 20, "source": "close"}'
                rows={2}
                className="font-mono text-sm"
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                기본값을 포함한 JSON 형식
              </p>
            </div>
          </div>
        </Card>
        
        {/* 코드 작성 */}
        <Card className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Python 코드</h2>
            <Button 
              type="button" 
              onClick={handleValidate} 
              disabled={isValidating}
              variant="outline"
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
          </div>
          
          <Textarea
            value={formData.code}
            onChange={e => setFormData({...formData, code: e.target.value})}
            rows={20}
            className="font-mono text-sm"
            required
          />
          
          <p className="text-xs text-muted-foreground mt-2">
            함수는 df(DataFrame)와 params(Dict)를 인자로 받아야 합니다
          </p>
          
          {/* 검증 결과 */}
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
                {validationResult.errors && validationResult.errors.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {validationResult.errors.map((err, i) => (
                      <li key={i} className="text-sm">• {err}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </Card>
        
        {/* 에러 메시지 */}
        {error && (
          <div className="p-4 bg-destructive/10 text-destructive rounded-lg flex items-start gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p>{error}</p>
          </div>
        )}
        
        {/* 제출 버튼 */}
        <div className="flex justify-end gap-4">
          <Button 
            type="button" 
            variant="outline" 
            onClick={() => router.back()}
            disabled={isSubmitting}
          >
            취소
          </Button>
          <Button 
            type="submit" 
            disabled={!validationResult?.is_valid || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                등록 중...
              </>
            ) : (
              '등록'
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}

