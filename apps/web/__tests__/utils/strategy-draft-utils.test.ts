/**
 * Strategy Draft Utils 테스트
 * 
 * Draft 생성 및 유틸 함수들이 올바르게 동작하는지 검증합니다.
 */

import { createEmptyDraft, createEmptyCondition } from '@/lib/strategy-draft-utils';

describe('Strategy Draft Utils', () => {
  
  describe('createEmptyDraft', () => {
    test('빈 Draft를 올바르게 생성', () => {
      const draft = createEmptyDraft();
      
      expect(draft.name).toBe('');
      expect(draft.description).toBe('');
      expect(draft.indicators).toEqual([]);
      expect(draft.entry.long.conditions).toEqual([]);
      expect(draft.entry.short.conditions).toEqual([]);
      expect(draft.stopLoss.type).toBe('fixed_percent');
      expect(draft.reverse.enabled).toBe(true);
      expect(draft.hook.enabled).toBe(false);
    });
    
    test('생성된 Draft의 기본값이 올바름', () => {
      const draft = createEmptyDraft();
      
      // Stop Loss 기본값
      if (draft.stopLoss.type === 'fixed_percent') {
        expect(draft.stopLoss.percent).toBe(2);
      }
      
      // Reverse 기본값
      if (draft.reverse.enabled) {
        expect(draft.reverse.mode).toBe('use_entry_opposite');
      }
    });
    
    test('여러 번 호출해도 독립적인 Draft 생성', () => {
      const draft1 = createEmptyDraft();
      const draft2 = createEmptyDraft();
      
      draft1.name = 'Strategy 1';
      draft2.name = 'Strategy 2';
      
      expect(draft1.name).toBe('Strategy 1');
      expect(draft2.name).toBe('Strategy 2');
      expect(draft1).not.toBe(draft2);
    });
  });
  
  describe('createEmptyCondition', () => {
    test('빈 조건을 올바르게 생성', () => {
      const condition = createEmptyCondition();
      
      expect(condition.tempId).toBeDefined();
      expect(typeof condition.tempId).toBe('string');
      expect(condition.left.type).toBe('indicator');
      expect(condition.left.value).toBe('');
      expect(condition.operator).toBe('>');
      expect(condition.right.type).toBe('indicator');
      expect(condition.right.value).toBe('');
    });
    
    test('각 조건마다 고유한 tempId 생성', () => {
      const condition1 = createEmptyCondition();
      const condition2 = createEmptyCondition();
      
      expect(condition1.tempId).not.toBe(condition2.tempId);
    });
    
    test('기본 연산자는 ">"', () => {
      const condition = createEmptyCondition();
      
      expect(condition.operator).toBe('>');
    });
  });
});

