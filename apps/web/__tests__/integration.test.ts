/**
 * 통합 테스트
 * 
 * 전략 빌더의 전체 플로우를 단위 테스트 레벨에서 검증
 */

import { StrategyDraft } from '@/types/strategy-draft';
import { createEmptyDraft, createEmptyCondition } from '@/lib/strategy-draft-utils';
import { validateDraft } from '@/lib/draft-validation';
import { draftToStrategyJSON } from '@/lib/draft-to-json';
import { calculateStrategyHash } from '@/lib/canonicalization';

describe('통합 테스트: 전체 플로우', () => {
  describe('시나리오 1: 간단한 EMA Cross 전략 생성', () => {
    test('빈 Draft → 지표 추가 → 조건 추가 → 저장', async () => {
      // 1. 빈 Draft 생성
      const draft = createEmptyDraft();
      expect(draft.indicators).toHaveLength(0);
      expect(draft.entry.long.conditions).toHaveLength(0);
      
      // 2. 전략 이름 입력
      draft.name = 'Simple EMA Cross';
      draft.description = 'Fast EMA crosses above Slow EMA';
      
      // 3. 지표 추가
      draft.indicators.push({
        id: 'ema_fast',
        type: 'ema',
        params: { source: 'close', period: 12 }
      });
      
      draft.indicators.push({
        id: 'ema_slow',
        type: 'ema',
        params: { source: 'close', period: 26 }
      });
      
      expect(draft.indicators).toHaveLength(2);
      
      // 4. 롱 진입 조건 추가
      const longCondition = createEmptyCondition();
      longCondition.left = { type: 'indicator', value: 'ema_fast' };
      longCondition.operator = 'cross_above';
      longCondition.right = { type: 'indicator', value: 'ema_slow' };
      
      draft.entry.long.conditions.push(longCondition);
      
      // 5. Validation
      const validationResult = validateDraft(draft);
      expect(validationResult.isValid).toBe(true);
      expect(validationResult.errors).toHaveLength(0);
      
      // 6. Draft → JSON 변환
      const strategyJSON = draftToStrategyJSON(draft);
      
      expect(strategyJSON.schema_version).toBe('1.0');
      expect(strategyJSON.meta.name).toBe('Simple EMA Cross');
      expect(strategyJSON.indicators).toHaveLength(2);
      expect(strategyJSON.entry.long.and).toHaveLength(1);
      expect(strategyJSON.entry.long.and[0].op).toBe('cross_above');
      
      // 7. strategy_hash 계산
      const hash = await calculateStrategyHash(strategyJSON);
      
      expect(hash).toBeDefined();
      expect(hash).toMatch(/^[a-f0-9]{64}$/);
    });
  });
  
  describe('시나리오 2: RSI 기반 전략 생성', () => {
    test('RSI 지표를 사용한 과매도/과매수 전략', async () => {
      const draft = createEmptyDraft();
      
      // 1. 전략 이름
      draft.name = 'RSI Oversold/Overbought';
      
      // 2. RSI 지표 추가
      draft.indicators.push({
        id: 'rsi_14',
        type: 'rsi',
        params: { source: 'close', period: 14 }
      });
      
      // 3. 롱 진입: RSI < 30 (과매도)
      const longCondition = createEmptyCondition();
      longCondition.left = { type: 'indicator', value: 'rsi_14' };
      longCondition.operator = '<';
      longCondition.right = { type: 'number', value: 30 };
      
      draft.entry.long.conditions.push(longCondition);
      
      // 4. 숏 진입: RSI > 70 (과매수)
      const shortCondition = createEmptyCondition();
      shortCondition.left = { type: 'indicator', value: 'rsi_14' };
      shortCondition.operator = '>';
      shortCondition.right = { type: 'number', value: 70 };
      
      draft.entry.short.conditions.push(shortCondition);
      
      // 5. Validation
      const validationResult = validateDraft(draft);
      expect(validationResult.isValid).toBe(true);
      
      // 6. JSON 변환
      const strategyJSON = draftToStrategyJSON(draft);
      
      expect(strategyJSON.entry.long.and).toHaveLength(1);
      expect(strategyJSON.entry.short.and).toHaveLength(1);
      
      // 롱 조건 검증
      expect(strategyJSON.entry.long.and[0].left).toEqual({ ref: 'rsi_14' });
      expect(strategyJSON.entry.long.and[0].op).toBe('<');
      expect(strategyJSON.entry.long.and[0].right).toEqual({ value: 30 });
      
      // 숏 조건 검증
      expect(strategyJSON.entry.short.and[0].left).toEqual({ ref: 'rsi_14' });
      expect(strategyJSON.entry.short.and[0].op).toBe('>');
      expect(strategyJSON.entry.short.and[0].right).toEqual({ value: 70 });
    });
  });
  
  describe('시나리오 3: 복합 조건 전략', () => {
    test('EMA + RSI 조합 전략 (AND 조건)', async () => {
      const draft = createEmptyDraft();
      
      draft.name = 'EMA + RSI Combined';
      
      // 지표 추가
      draft.indicators.push(
        { id: 'ema_20', type: 'ema', params: { source: 'close', period: 20 } },
        { id: 'ema_50', type: 'ema', params: { source: 'close', period: 50 } },
        { id: 'rsi_14', type: 'rsi', params: { source: 'close', period: 14 } }
      );
      
      // 롱 진입: EMA20 > EMA50 AND RSI < 30
      const condition1 = createEmptyCondition();
      condition1.left = { type: 'indicator', value: 'ema_20' };
      condition1.operator = '>';
      condition1.right = { type: 'indicator', value: 'ema_50' };
      
      const condition2 = createEmptyCondition();
      condition2.left = { type: 'indicator', value: 'rsi_14' };
      condition2.operator = '<';
      condition2.right = { type: 'number', value: 30 };
      
      draft.entry.long.conditions.push(condition1, condition2);
      
      // Validation
      const validationResult = validateDraft(draft);
      expect(validationResult.isValid).toBe(true);
      
      // JSON 변환
      const strategyJSON = draftToStrategyJSON(draft);
      
      expect(strategyJSON.indicators).toHaveLength(3);
      expect(strategyJSON.entry.long.and).toHaveLength(2);
    });
  });
  
  describe('시나리오 4: ATR 기반 손절 전략', () => {
    test('ATR을 사용한 동적 손절', async () => {
      const draft = createEmptyDraft();
      
      draft.name = 'ATR-based Stop Loss';
      
      // 지표 추가
      draft.indicators.push(
        { id: 'ema_20', type: 'ema', params: { source: 'close', period: 20 } },
        { id: 'atr_14', type: 'atr', params: { period: 14 } }
      );
      
      // 진입 조건 (간단한 예)
      const condition = createEmptyCondition();
      condition.left = { type: 'indicator', value: 'ema_20' };
      condition.operator = '>';
      condition.right = { type: 'number', value: 50000 };
      
      draft.entry.long.conditions.push(condition);
      
      // ATR 기반 손절
      draft.stopLoss = {
        type: 'atr_based',
        atr_indicator_id: 'atr_14',
        multiplier: 2
      };
      
      // Validation
      const validationResult = validateDraft(draft);
      expect(validationResult.isValid).toBe(true);
      
      // JSON 변환
      const strategyJSON = draftToStrategyJSON(draft);
      
      expect(strategyJSON.stop_loss).toEqual({
        type: 'atr_based',
        atr_indicator_id: 'atr_14',
        multiplier: 2
      });
    });
  });
  
  describe('시나리오 5: Validation 실패 케이스', () => {
    test('전략 이름이 없으면 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = ''; // 빈 이름
      
      // 지표와 조건은 추가
      draft.indicators.push({
        id: 'ema_1',
        type: 'ema',
        params: { source: 'close', period: 20 }
      });
      
      const condition = createEmptyCondition();
      condition.left = { type: 'indicator', value: 'ema_1' };
      condition.operator = '>';
      condition.right = { type: 'number', value: 0 };
      draft.entry.long.conditions.push(condition);
      
      const validationResult = validateDraft(draft);
      
      expect(validationResult.isValid).toBe(false);
      expect(validationResult.errors.some(e => e.field === 'name')).toBe(true);
    });
    
    test('진입 조건이 없으면 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = 'No Entry Conditions';
      
      // 지표는 있지만 조건 없음
      draft.indicators.push({
        id: 'ema_1',
        type: 'ema',
        params: { source: 'close', period: 20 }
      });
      
      const validationResult = validateDraft(draft);
      
      expect(validationResult.isValid).toBe(false);
      expect(validationResult.errors.some(e => e.field === 'entry')).toBe(true);
    });
    
    test('cross 연산자에 숫자 사용 시 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = 'Invalid Cross';
      
      draft.indicators.push({
        id: 'ema_1',
        type: 'ema',
        params: { source: 'close', period: 20 }
      });
      
      // cross_above 연산자에 숫자 사용 (잘못된 경우)
      const condition = createEmptyCondition();
      condition.left = { type: 'number', value: 50 };
      condition.operator = 'cross_above';
      condition.right = { type: 'indicator', value: 'ema_1' };
      
      draft.entry.long.conditions.push(condition);
      
      const validationResult = validateDraft(draft);
      
      expect(validationResult.isValid).toBe(false);
      expect(validationResult.errors.some(e => e.message.includes('cross'))).toBe(true);
    });
    
    test('존재하지 않는 ATR 지표 사용 시 Validation 실패', () => {
      const draft = createEmptyDraft();
      draft.name = 'Missing ATR';
      
      draft.indicators.push({
        id: 'ema_1',
        type: 'ema',
        params: { source: 'close', period: 20 }
      });
      
      const condition = createEmptyCondition();
      condition.left = { type: 'indicator', value: 'ema_1' };
      condition.operator = '>';
      condition.right = { type: 'number', value: 0 };
      draft.entry.long.conditions.push(condition);
      
      // ATR 지표 없이 ATR 기반 손절 사용
      draft.stopLoss = {
        type: 'atr_based',
        atr_indicator_id: 'atr_14',
        multiplier: 2
      };
      
      const validationResult = validateDraft(draft);
      
      expect(validationResult.isValid).toBe(false);
      expect(validationResult.errors.some(e => e.field === 'stopLoss')).toBe(true);
    });
  });
  
  describe('시나리오 6: Reverse 설정', () => {
    test('Reverse 활성화 시 JSON에 반영된다', () => {
      const draft = createEmptyDraft();
      draft.name = 'Reverse Enabled';
      
      draft.indicators.push({
        id: 'ema_1',
        type: 'ema',
        params: { source: 'close', period: 20 }
      });
      
      const condition = createEmptyCondition();
      condition.left = { type: 'indicator', value: 'ema_1' };
      condition.operator = '>';
      condition.right = { type: 'number', value: 0 };
      draft.entry.long.conditions.push(condition);
      
      // Reverse 활성화 (기본값)
      draft.reverse = {
        enabled: true,
        mode: 'use_entry_opposite'
      };
      
      const strategyJSON = draftToStrategyJSON(draft);
      
      expect(strategyJSON.reverse).toEqual({
        enabled: true,
        mode: 'use_entry_opposite'
      });
    });
    
    test('Reverse 비활성화 시 JSON에 반영된다', () => {
      const draft = createEmptyDraft();
      draft.name = 'Reverse Disabled';
      
      draft.indicators.push({
        id: 'ema_1',
        type: 'ema',
        params: { source: 'close', period: 20 }
      });
      
      const condition = createEmptyCondition();
      condition.left = { type: 'indicator', value: 'ema_1' };
      condition.operator = '>';
      condition.right = { type: 'number', value: 0 };
      draft.entry.long.conditions.push(condition);
      
      // Reverse 비활성화
      draft.reverse = { enabled: false };
      
      const strategyJSON = draftToStrategyJSON(draft);
      
      expect(strategyJSON.reverse).toEqual({ enabled: false });
    });
  });
  
  describe('시나리오 7: 복잡한 실전 전략', () => {
    test('멀티 인디케이터 + 복합 조건 + ATR 손절', async () => {
      const draft = createEmptyDraft();
      
      // 메타 정보
      draft.name = 'Advanced Multi-Indicator Strategy';
      draft.description = 'Combines EMA, SMA, RSI, and ATR for robust trading';
      
      // 여러 지표 추가
      draft.indicators.push(
        { id: 'ema_12', type: 'ema', params: { source: 'close', period: 12 } },
        { id: 'ema_26', type: 'ema', params: { source: 'close', period: 26 } },
        { id: 'sma_50', type: 'sma', params: { source: 'close', period: 50 } },
        { id: 'rsi_14', type: 'rsi', params: { source: 'close', period: 14 } },
        { id: 'atr_14', type: 'atr', params: { period: 14 } }
      );
      
      // 롱 진입: EMA12 > EMA26 AND EMA26 > SMA50 AND RSI > 50
      const longCond1 = createEmptyCondition();
      longCond1.left = { type: 'indicator', value: 'ema_12' };
      longCond1.operator = '>';
      longCond1.right = { type: 'indicator', value: 'ema_26' };
      
      const longCond2 = createEmptyCondition();
      longCond2.left = { type: 'indicator', value: 'ema_26' };
      longCond2.operator = '>';
      longCond2.right = { type: 'indicator', value: 'sma_50' };
      
      const longCond3 = createEmptyCondition();
      longCond3.left = { type: 'indicator', value: 'rsi_14' };
      longCond3.operator = '>';
      longCond3.right = { type: 'number', value: 50 };
      
      draft.entry.long.conditions.push(longCond1, longCond2, longCond3);
      
      // 숏 진입: EMA12 < EMA26 AND EMA26 < SMA50 AND RSI < 50
      const shortCond1 = createEmptyCondition();
      shortCond1.left = { type: 'indicator', value: 'ema_12' };
      shortCond1.operator = '<';
      shortCond1.right = { type: 'indicator', value: 'ema_26' };
      
      const shortCond2 = createEmptyCondition();
      shortCond2.left = { type: 'indicator', value: 'ema_26' };
      shortCond2.operator = '<';
      shortCond2.right = { type: 'indicator', value: 'sma_50' };
      
      const shortCond3 = createEmptyCondition();
      shortCond3.left = { type: 'indicator', value: 'rsi_14' };
      shortCond3.operator = '<';
      shortCond3.right = { type: 'number', value: 50 };
      
      draft.entry.short.conditions.push(shortCond1, shortCond2, shortCond3);
      
      // ATR 기반 손절
      draft.stopLoss = {
        type: 'atr_based',
        atr_indicator_id: 'atr_14',
        multiplier: 2.5
      };
      
      // Reverse 활성화
      draft.reverse = {
        enabled: true,
        mode: 'use_entry_opposite'
      };
      
      // Validation
      const validationResult = validateDraft(draft);
      expect(validationResult.isValid).toBe(true);
      expect(validationResult.errors).toHaveLength(0);
      
      // JSON 변환
      const strategyJSON = draftToStrategyJSON(draft);
      
      expect(strategyJSON.schema_version).toBe('1.0');
      expect(strategyJSON.indicators).toHaveLength(5);
      expect(strategyJSON.entry.long.and).toHaveLength(3);
      expect(strategyJSON.entry.short.and).toHaveLength(3);
      expect(strategyJSON.stop_loss.type).toBe('atr_based');
      expect(strategyJSON.reverse.enabled).toBe(true);
      
      // strategy_hash 계산
      const hash = await calculateStrategyHash(strategyJSON);
      expect(hash).toMatch(/^[a-f0-9]{64}$/);
      
      // 동일한 전략을 다시 생성해도 동일한 hash
      const draft2 = JSON.parse(JSON.stringify(draft));
      draft2.name = 'Different Name'; // 이름만 변경
      const json2 = draftToStrategyJSON(draft2);
      const hash2 = await calculateStrategyHash(json2);
      
      expect(hash2).toBe(hash); // meta를 제외하면 동일하므로 hash도 동일
    });
  });
});

