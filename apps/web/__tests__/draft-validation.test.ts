/**
 * Draft Validation 단위 테스트
 * 
 * PRD/TRD 규칙에 따른 Validation 로직을 검증합니다.
 */

import { validateDraft } from '@/lib/draft-validation';
import { createEmptyDraft, createEmptyCondition } from '@/lib/strategy-draft-utils';
import { StrategyDraft } from '@/types/strategy-draft';

describe('Draft Validation', () => {
  
  describe('전략 이름 검증', () => {
    test('빈 이름은 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = '';
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.field === 'name')).toBe(true);
      expect(result.errors.find(e => e.field === 'name')?.message).toContain('필수');
    });
    
    test('공백만 있는 이름은 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = '   ';
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.field === 'name')).toBe(true);
    });
    
    test('유효한 이름은 Validation 통과 (다른 조건 충족 시)', () => {
      const draft = createEmptyDraft();
      draft.name = 'Valid Strategy Name';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: 'ema_1' },
          operator: '>',
          right: { type: 'number', value: 100 }
        }
      ];
      
      const result = validateDraft(draft);
      
      expect(result.errors.find(e => e.field === 'name')).toBeUndefined();
    });
  });
  
  describe('Indicator ID 중복 검증', () => {
    test('중복된 Indicator ID는 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 26 } }
      ];
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.field === 'indicators')).toBe(true);
      expect(result.errors.find(e => e.field === 'indicators')?.message).toContain('중복');
    });
    
    test('고유한 Indicator ID는 Validation 통과', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
        { id: 'ema_2', type: 'ema', params: { source: 'close', period: 26 } }
      ];
      draft.entry.long.conditions = [createEmptyCondition()];
      draft.entry.long.conditions[0].left = { type: 'indicator', value: 'ema_1' };
      draft.entry.long.conditions[0].right = { type: 'indicator', value: 'ema_2' };
      
      const result = validateDraft(draft);
      
      expect(result.errors.find(e => e.field === 'indicators')).toBeUndefined();
    });
  });
  
  describe('Entry 조건 검증', () => {
    test('롱/숏 조건이 모두 없으면 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [];
      draft.entry.short.conditions = [];
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.field === 'entry')).toBe(true);
      expect(result.errors.find(e => e.field === 'entry')?.message).toContain('최소 1개');
    });
    
    test('롱 조건만 있으면 Validation 통과', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: 'ema_1' },
          operator: '>',
          right: { type: 'number', value: 100 }
        }
      ];
      draft.entry.short.conditions = [];
      
      const result = validateDraft(draft);
      
      // entry 필드에 대한 에러가 없어야 함 (최소 1개 조건 충족)
      const entryErrors = result.errors.filter(e => 
        e.field === 'entry' && e.message.includes('최소 1개')
      );
      expect(entryErrors.length).toBe(0);
    });
    
    test('숏 조건만 있으면 Validation 통과', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [];
      draft.entry.short.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: 'ema_1' },
          operator: '<',
          right: { type: 'number', value: 100 }
        }
      ];
      
      const result = validateDraft(draft);
      
      const entryErrors = result.errors.filter(e => 
        e.field === 'entry' && e.message.includes('최소 1개')
      );
      expect(entryErrors.length).toBe(0);
    });
  });
  
  describe('Condition 좌변/우변 검증', () => {
    test('좌변이 비어있으면 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: '' },
          operator: '>',
          right: { type: 'number', value: 100 }
        }
      ];
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.message.includes('좌변'))).toBe(true);
    });
    
    test('우변이 비어있으면 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: 'ema_1' },
          operator: '>',
          right: { type: 'indicator', value: '' }
        }
      ];
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.message.includes('우변'))).toBe(true);
    });
  });
  
  describe('cross 연산자 검증', () => {
    test('cross_above 연산자는 양쪽 모두 지표여야 함', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'number', value: 50 },
          operator: 'cross_above',
          right: { type: 'indicator', value: 'ema_1' }
        }
      ];
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.message.includes('cross'))).toBe(true);
      expect(result.errors.some(e => e.message.includes('지표'))).toBe(true);
    });
    
    test('cross_below 연산자는 양쪽 모두 지표여야 함', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: 'ema_1' },
          operator: 'cross_below',
          right: { type: 'number', value: 50 }
        }
      ];
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.message.includes('cross'))).toBe(true);
    });
    
    test('cross 연산자에 양쪽 모두 지표면 Validation 통과', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
        { id: 'ema_2', type: 'ema', params: { source: 'close', period: 26 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: 'ema_1' },
          operator: 'cross_above',
          right: { type: 'indicator', value: 'ema_2' }
        }
      ];
      
      const result = validateDraft(draft);
      
      const crossErrors = result.errors.filter(e => e.message.includes('cross'));
      expect(crossErrors.length).toBe(0);
    });
  });
  
  describe('Stop Loss 검증', () => {
    test('ATR 기반 SL이지만 ATR 지표가 없으면 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: 'ema_1' },
          operator: '>',
          right: { type: 'number', value: 100 }
        }
      ];
      draft.stopLoss = {
        type: 'atr_based',
        atr_indicator_id: 'atr_1',
        multiplier: 2
      };
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.field === 'stopLoss')).toBe(true);
      expect(result.errors.some(e => e.message.includes('ATR'))).toBe(true);
    });
    
    test('ATR 기반 SL이고 ATR 지표가 있으면 Validation 통과', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
        { id: 'atr_1', type: 'atr', params: { period: 14 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: 'ema_1' },
          operator: '>',
          right: { type: 'number', value: 100 }
        }
      ];
      draft.stopLoss = {
        type: 'atr_based',
        atr_indicator_id: 'atr_1',
        multiplier: 2
      };
      
      const result = validateDraft(draft);
      
      const slErrors = result.errors.filter(e => 
        e.field === 'stopLoss' && e.message.includes('ATR')
      );
      expect(slErrors.length).toBe(0);
    });
    
    test('Fixed Percent SL은 항상 Validation 통과', () => {
      const draft = createEmptyDraft();
      draft.name = 'Test Strategy';
      draft.indicators = [
        { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
      ];
      draft.entry.long.conditions = [
        {
          tempId: '1',
          left: { type: 'indicator', value: 'ema_1' },
          operator: '>',
          right: { type: 'number', value: 100 }
        }
      ];
      draft.stopLoss = {
        type: 'fixed_percent',
        percent: 2
      };
      
      const result = validateDraft(draft);
      
      const slErrors = result.errors.filter(e => e.field === 'stopLoss');
      expect(slErrors.length).toBe(0);
    });
  });
  
  describe('완전한 Draft Validation', () => {
    test('모든 조건을 만족하는 Draft는 Validation 통과', () => {
      const draft: StrategyDraft = {
        name: 'Simple EMA Cross Strategy',
        description: 'EMA 12와 26의 교차를 이용한 전략',
        indicators: [
          { id: 'ema_fast', type: 'ema', params: { source: 'close', period: 12 } },
          { id: 'ema_slow', type: 'ema', params: { source: 'close', period: 26 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_fast' },
                operator: 'cross_above',
                right: { type: 'indicator', value: 'ema_slow' }
              }
            ]
          },
          short: {
            conditions: [
              {
                tempId: '2',
                left: { type: 'indicator', value: 'ema_fast' },
                operator: 'cross_below',
                right: { type: 'indicator', value: 'ema_slow' }
              }
            ]
          }
        },
        stopLoss: {
          type: 'fixed_percent',
          percent: 2
        },
        reverse: {
          enabled: true,
          mode: 'use_entry_opposite'
        },
        hook: {
          enabled: false
        }
      };
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(true);
      expect(result.errors.length).toBe(0);
    });
    
    test('빈 Draft는 여러 Validation 에러 반환', () => {
      const draft = createEmptyDraft();
      
      const result = validateDraft(draft);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      // 최소한 이름과 진입 조건 에러가 있어야 함
      expect(result.errors.some(e => e.field === 'name')).toBe(true);
      expect(result.errors.some(e => e.field === 'entry')).toBe(true);
    });
  });
});

