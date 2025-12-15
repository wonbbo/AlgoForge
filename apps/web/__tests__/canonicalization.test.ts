/**
 * Canonicalization 테스트
 * 
 * Strategy JSON의 정규화(Canonicalization)가 올바르게 동작하는지 검증합니다.
 * 동일한 전략은 항상 동일한 hash를 생성해야 합니다.
 */

import { canonicalizeStrategyJSON, calculateStrategyHash } from '@/lib/draft-to-json';
import type { StrategyJSON } from '@/lib/draft-to-json';

describe('Canonicalization', () => {
  
  describe('canonicalizeStrategyJSON', () => {
    test('meta 필드는 제외되어야 함', () => {
      const json: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'Test Strategy',
          description: 'This should be excluded'
        },
        indicators: [],
        entry: {
          long: { and: [] },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const canonical = canonicalizeStrategyJSON(json);
      
      expect(canonical).not.toContain('Test Strategy');
      expect(canonical).not.toContain('This should be excluded');
    });
    
    test('key가 알파벳 순으로 정렬되어야 함', () => {
      const json: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'Test',
          description: ''
        },
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: { and: [] },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const canonical = canonicalizeStrategyJSON(json);
      const parsed = JSON.parse(canonical);
      
      // 최상위 key가 정렬되어 있는지 확인
      const keys = Object.keys(parsed);
      const sortedKeys = [...keys].sort();
      expect(keys).toEqual(sortedKeys);
    });
    
    test('중첩된 객체의 key도 정렬되어야 함', () => {
      const json: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'Test',
          description: ''
        },
        indicators: [
          {
            id: 'ema_1',
            type: 'ema',
            params: { period: 12, source: 'close' } // 의도적으로 역순
          }
        ],
        entry: {
          long: { and: [] },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const canonical = canonicalizeStrategyJSON(json);
      const parsed = JSON.parse(canonical);
      
      // params의 key가 정렬되어 있는지 확인
      const paramsKeys = Object.keys(parsed.indicators[0].params);
      expect(paramsKeys).toEqual(['period', 'source']);
    });
    
    test('동일한 내용이지만 meta가 다른 경우 동일한 canonical', () => {
      const json1: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'Strategy A',
          description: 'Description A'
        },
        indicators: [],
        entry: {
          long: { and: [] },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json2: StrategyJSON = {
        ...json1,
        meta: {
          name: 'Strategy B',
          description: 'Description B'
        }
      };
      
      const canonical1 = canonicalizeStrategyJSON(json1);
      const canonical2 = canonicalizeStrategyJSON(json2);
      
      expect(canonical1).toBe(canonical2);
    });
    
    test('key 순서가 다른 경우에도 동일한 canonical', () => {
      // 의도적으로 다른 순서로 작성
      const json1: any = {
        schema_version: '1.0',
        meta: { name: 'Test', description: '' },
        indicators: [],
        entry: {
          long: { and: [] },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json2: any = {
        hook: { enabled: false },
        reverse: { enabled: false },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        entry: {
          short: { and: [] },
          long: { and: [] }
        },
        indicators: [],
        meta: { name: 'Test', description: '' },
        schema_version: '1.0'
      };
      
      const canonical1 = canonicalizeStrategyJSON(json1);
      const canonical2 = canonicalizeStrategyJSON(json2);
      
      expect(canonical1).toBe(canonical2);
    });
  });
  
  describe('calculateStrategyHash', () => {
    test('SHA-256 hash는 64자 hex string이어야 함', async () => {
      const json: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'Test',
          description: ''
        },
        indicators: [],
        entry: {
          long: { and: [] },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const hash = await calculateStrategyHash(json);
      
      expect(hash).toHaveLength(64);
      expect(/^[0-9a-f]{64}$/.test(hash)).toBe(true);
    });
    
    test('동일한 JSON은 동일한 hash 생성', async () => {
      const json: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'Test',
          description: ''
        },
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: {
            and: [
              {
                left: { ref: 'ema_1' },
                op: '>',
                right: { value: 100 }
              }
            ]
          },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const hash1 = await calculateStrategyHash(json);
      const hash2 = await calculateStrategyHash(json);
      
      expect(hash1).toBe(hash2);
    });
    
    test('meta만 다른 경우 동일한 hash', async () => {
      const json1: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'Strategy A',
          description: 'Description A'
        },
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: {
            and: [
              {
                left: { ref: 'ema_1' },
                op: '>',
                right: { value: 100 }
              }
            ]
          },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json2: StrategyJSON = {
        ...json1,
        meta: {
          name: 'Strategy B',
          description: 'Description B'
        }
      };
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      expect(hash1).toBe(hash2);
    });
    
    test('실제 내용이 다르면 다른 hash', async () => {
      const json1: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'Test',
          description: ''
        },
        indicators: [],
        entry: {
          long: { and: [] },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json2: StrategyJSON = {
        ...json1,
        stop_loss: { type: 'fixed_percent', percent: 3 } // 다른 값
      };
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      expect(hash1).not.toBe(hash2);
    });
    
    test('지표 순서가 다르면 다른 hash', async () => {
      const json1: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'Test',
          description: ''
        },
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
          { id: 'ema_2', type: 'ema', params: { source: 'close', period: 26 } }
        ],
        entry: {
          long: { and: [] },
          short: { and: [] }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json2: StrategyJSON = {
        ...json1,
        indicators: [
          { id: 'ema_2', type: 'ema', params: { source: 'close', period: 26 } },
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ]
      };
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      // 배열 순서가 다르므로 hash도 달라야 함
      expect(hash1).not.toBe(hash2);
    });
  });
  
  describe('결정성 보장', () => {
    test('같은 전략을 여러 번 hash해도 동일한 결과', async () => {
      const json: StrategyJSON = {
        schema_version: '1.0',
        meta: {
          name: 'EMA Cross',
          description: 'Simple EMA crossover'
        },
        indicators: [
          { id: 'ema_fast', type: 'ema', params: { source: 'close', period: 12 } },
          { id: 'ema_slow', type: 'ema', params: { source: 'close', period: 26 } }
        ],
        entry: {
          long: {
            and: [
              {
                left: { ref: 'ema_fast' },
                op: 'cross_above',
                right: { ref: 'ema_slow' }
              }
            ]
          },
          short: {
            and: [
              {
                left: { ref: 'ema_fast' },
                op: 'cross_below',
                right: { ref: 'ema_slow' }
              }
            ]
          }
        },
        stop_loss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: true, mode: 'use_entry_opposite' },
        hook: { enabled: false }
      };
      
      // 100번 hash 계산
      const hashes: string[] = [];
      for (let i = 0; i < 100; i++) {
        const hash = await calculateStrategyHash(json);
        hashes.push(hash);
      }
      
      // 모든 hash가 동일해야 함
      const uniqueHashes = new Set(hashes);
      expect(uniqueHashes.size).toBe(1);
    });
  });
});

