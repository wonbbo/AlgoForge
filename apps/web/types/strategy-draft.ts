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
  
  // 진출 조건 (Step 3) - 선택사항
  exit: ExitDraft;
  
  // 손절 (Step 4)
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
  
  // 지표 타입 (내장 지표 또는 커스텀 지표 타입)
  type: string;
  
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
 * ADX 지표 예시
 */
export interface ADXIndicator {
  id: string;
  type: 'adx';
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
 * 예: "close" > "ema_20" (OHLCV 사용)
 */
export interface ConditionDraft {
  // 임시 ID (UI 렌더링용)
  tempId: string;
  
  // 좌변
  left: {
    type: 'indicator' | 'price' | 'number';
    value: string | number;  // indicator면 id, price면 'open'|'high'|'low'|'close'|'volume', number면 숫자
  };
  
  // 연산자
  operator: '>' | '<' | '>=' | '<=' | 'cross_above' | 'cross_below';
  
  // 우변
  right: {
    type: 'indicator' | 'price' | 'number';
    value: string | number;
  };
}

/**
 * 손절 Draft
 * 
 * - fixed_percent: 진입가 대비 고정 퍼센트로 손절선 설정
 * - atr_based: ATR 지표를 활용한 동적 손절선 설정
 * - indicator_level: 사용자 지표 값을 손절가(가격 레벨)로 직접 사용
 */
export type StopLossDraft = 
  | { type: 'fixed_percent'; percent: number }
  | { type: 'atr_based'; atr_indicator_id: string; multiplier: number }
  | { type: 'indicator_level'; long_ref: string; short_ref: string };

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
 * 진출 조건 Draft
 * 
 * - indicatorBased: 지표 기반 진출 조건 (예: close가 ema200에 닿으면 청산)
 * - atrTrailing: ATR 기반 Trailing Stop (TP1 달성 후 활성화)
 * 
 * 둘 다 사용 가능하며, 먼저 충족되는 조건으로 청산
 * 둘 다 비활성화 시 기존 동작 유지 (반대 진입 신호로 청산)
 */
export interface ExitDraft {
  // 지표 기반 진출 조건 (선택)
  indicatorBased: {
    enabled: boolean;
    long: {
      conditions: ConditionDraft[];  // AND 조건 (롱 포지션 청산 조건)
    };
    short: {
      conditions: ConditionDraft[];  // AND 조건 (숏 포지션 청산 조건)
    };
  };
  // ATR Trailing Stop (선택, TP1 달성 후 활성화)
  atrTrailing: {
    enabled: boolean;
    atr_indicator_id: string;  // Step1에서 정의한 ATR 지표 ID
    multiplier: number;        // ATR 배수 (기본 2.0)
  };
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

