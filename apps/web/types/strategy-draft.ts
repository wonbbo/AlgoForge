/**
 * 전략 빌더 Draft State 타입 정의
 * 
 * UI 전용 상태로, 최종적으로 Strategy JSON Schema v1.0으로 변환됨
 */

/**
 * 전략 빌더 Draft State
 */
export interface StrategyDraft {
  // 메타 정보
  name: string;
  description: string;
  
  // 지표 (Step 1)
  indicators: IndicatorDraft[];
  
  // 진입 조건 (Step 2)
  entry: EntryDraft;
  
  // 손절 (Step 3)
  stopLoss: StopLossDraft;
  
  // Reverse (Advanced)
  reverse: ReverseDraft;
  
  // Hook (Advanced)
  hook: HookDraft;
}

/**
 * 지표 Draft
 */
export interface IndicatorDraft {
  // 고유 ID (사용자가 중복 불가하게 입력 또는 자동 생성)
  id: string;
  
  // 지표 타입
  type: 'ema' | 'sma' | 'rsi' | 'atr' | 'price' | 'candle';
  
  // 파라미터 (지표 타입에 따라 다름)
  params: Record<string, any>;
}

/**
 * EMA 지표 예시
 */
export interface EMAIndicator {
  id: string;
  type: 'ema';
  params: {
    source: 'close' | 'open' | 'high' | 'low';
    period: number;
  };
}

/**
 * SMA 지표 예시
 */
export interface SMAIndicator {
  id: string;
  type: 'sma';
  params: {
    source: 'close' | 'open' | 'high' | 'low';
    period: number;
  };
}

/**
 * RSI 지표 예시
 */
export interface RSIIndicator {
  id: string;
  type: 'rsi';
  params: {
    source: 'close';
    period: number;
  };
}

/**
 * ATR 지표 예시
 */
export interface ATRIndicator {
  id: string;
  type: 'atr';
  params: {
    period: number;
  };
}

/**
 * 진입 조건 Draft
 */
export interface EntryDraft {
  long: {
    conditions: ConditionDraft[];  // AND 조건
  };
  short: {
    conditions: ConditionDraft[];  // AND 조건
  };
}

/**
 * 조건 Draft
 * 
 * 예: "ema_fast" > "ema_slow"
 */
export interface ConditionDraft {
  // 임시 ID (UI 렌더링용)
  tempId: string;
  
  // 좌변
  left: {
    type: 'indicator' | 'number';
    value: string | number;  // indicator면 id, number면 숫자
  };
  
  // 연산자
  operator: '>' | '<' | '>=' | '<=' | 'cross_above' | 'cross_below';
  
  // 우변
  right: {
    type: 'indicator' | 'number';
    value: string | number;
  };
}

/**
 * 손절 Draft
 */
export type StopLossDraft = 
  | { type: 'fixed_percent'; percent: number }
  | { type: 'atr_based'; atr_indicator_id: string; multiplier: number };

/**
 * Reverse Draft
 */
export type ReverseDraft = 
  | { enabled: false }
  | { enabled: true; mode: 'use_entry_opposite' }
  | { enabled: true; mode: 'custom'; custom_conditions: any };  // v2

/**
 * Hook Draft
 */
export interface HookDraft {
  enabled: boolean;
  // Hook 관련 설정 (MVP에서는 OFF 기본)
}

/**
 * Validation 에러
 */
export interface ValidationError {
  field: string;
  message: string;
}

/**
 * Validation 결과
 */
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

