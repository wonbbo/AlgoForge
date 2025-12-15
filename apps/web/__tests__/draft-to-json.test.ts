/**
 * Draft → JSON 변환 통합 테스트
 * 
 * Draft State가 Strategy JSON Schema v1.0에 맞게 변환되는지 검증합니다.
 */

import { draftToStrategyJSON, canonicalizeStrategyJSON, calculateStrategyHash } from '@/lib/draft-to-json';
import { StrategyDraft } from '@/types/strategy-draft';

describe('Draft to JSON Conversion', () => {
  
  describe('기본 변환 테스트', () => {
    test('최소 Draft → JSON 변환', () => {
      const draft: StrategyDraft = {
        name: 'Minimal Strategy',
        description: 'Test',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'number', value: 100 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      expect(json.schema_version).toBe('1.0');
      expect(json.meta.name).toBe('Minimal Strategy');
      expect(json.meta.description).toBe('Test');
      expect(json.indicators.length).toBe(1);
      expect(json.indicators[0].id).toBe('ema_1');
      expect(json.entry.long.and.length).toBe(1);
      expect(json.entry.short.and.length).toBe(0);
      expect(json.stop_loss.type).toBe('fixed_percent');
      expect(json.reverse.enabled).toBe(false);
      expect(json.hook.enabled).toBe(false);
    });
    
    test('EMA Cross Strategy 변환', () => {
      const draft: StrategyDraft = {
        name: 'EMA Cross Strategy',
        description: 'Simple EMA crossover strategy',
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
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: true, mode: 'use_entry_opposite' },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      expect(json.schema_version).toBe('1.0');
      expect(json.indicators.length).toBe(2);
      expect(json.entry.long.and[0].op).toBe('cross_above');
      expect(json.entry.short.and[0].op).toBe('cross_below');
      expect(json.reverse.enabled).toBe(true);
      if ('mode' in json.reverse) {
        expect(json.reverse.mode).toBe('use_entry_opposite');
      }
    });
  });
  
  describe('Indicator 변환 테스트', () => {
    test('여러 지표 타입 변환', () => {
      const draft: StrategyDraft = {
        name: 'Multi Indicator Strategy',
        description: '',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
          { id: 'sma_1', type: 'sma', params: { source: 'close', period: 50 } },
          { id: 'rsi_1', type: 'rsi', params: { source: 'close', period: 14 } },
          { id: 'atr_1', type: 'atr', params: { period: 14 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'indicator', value: 'sma_1' }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      expect(json.indicators.length).toBe(4);
      expect(json.indicators[0].type).toBe('ema');
      expect(json.indicators[1].type).toBe('sma');
      expect(json.indicators[2].type).toBe('rsi');
      expect(json.indicators[3].type).toBe('atr');
    });
    
    test('지표 순서 유지', () => {
      const draft: StrategyDraft = {
        name: 'Order Test',
        description: '',
        indicators: [
          { id: 'third', type: 'ema', params: { source: 'close', period: 50 } },
          { id: 'first', type: 'ema', params: { source: 'close', period: 10 } },
          { id: 'second', type: 'ema', params: { source: 'close', period: 20 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'first' },
                operator: '>',
                right: { type: 'number', value: 100 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      // 입력 순서 그대로 유지되어야 함
      expect(json.indicators[0].id).toBe('third');
      expect(json.indicators[1].id).toBe('first');
      expect(json.indicators[2].id).toBe('second');
    });
  });
  
  describe('Condition 변환 테스트', () => {
    test('지표 간 비교 조건 변환', () => {
      const draft: StrategyDraft = {
        name: 'Test',
        description: '',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
          { id: 'ema_2', type: 'ema', params: { source: 'close', period: 26 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'indicator', value: 'ema_2' }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      const condition = json.entry.long.and[0];
      expect('ref' in condition.left && condition.left.ref).toBe('ema_1');
      expect(condition.op).toBe('>');
      expect('ref' in condition.right && condition.right.ref).toBe('ema_2');
    });
    
    test('지표와 숫자 비교 조건 변환', () => {
      const draft: StrategyDraft = {
        name: 'Test',
        description: '',
        indicators: [
          { id: 'rsi_1', type: 'rsi', params: { source: 'close', period: 14 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'rsi_1' },
                operator: '>',
                right: { type: 'number', value: 70 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      const condition = json.entry.long.and[0];
      expect('ref' in condition.left && condition.left.ref).toBe('rsi_1');
      expect('value' in condition.right && condition.right.value).toBe(70);
    });
    
    test('복수 조건 (AND) 변환', () => {
      const draft: StrategyDraft = {
        name: 'Test',
        description: '',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
          { id: 'rsi_1', type: 'rsi', params: { source: 'close', period: 14 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'number', value: 100 }
              },
              {
                tempId: '2',
                left: { type: 'indicator', value: 'rsi_1' },
                operator: '<',
                right: { type: 'number', value: 30 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      expect(json.entry.long.and.length).toBe(2);
      expect(json.entry.long.and[0].op).toBe('>');
      expect(json.entry.long.and[1].op).toBe('<');
    });
  });
  
  describe('Stop Loss 변환 테스트', () => {
    test('Fixed Percent SL 변환', () => {
      const draft: StrategyDraft = {
        name: 'Test',
        description: '',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'number', value: 100 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 3 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      expect(json.stop_loss.type).toBe('fixed_percent');
      if ('percent' in json.stop_loss) {
        expect(json.stop_loss.percent).toBe(3);
      }
    });
    
    test('ATR Based SL 변환', () => {
      const draft: StrategyDraft = {
        name: 'Test',
        description: '',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
          { id: 'atr_1', type: 'atr', params: { period: 14 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'number', value: 100 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: {
          type: 'atr_based',
          atr_indicator_id: 'atr_1',
          multiplier: 2.5
        },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      expect(json.stop_loss.type).toBe('atr_based');
      if ('atr_indicator_id' in json.stop_loss) {
        expect(json.stop_loss.atr_indicator_id).toBe('atr_1');
        expect(json.stop_loss.multiplier).toBe(2.5);
      }
    });
  });
  
  describe('Reverse 변환 테스트', () => {
    test('Reverse 비활성화', () => {
      const draft: StrategyDraft = {
        name: 'Test',
        description: '',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'number', value: 100 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      expect(json.reverse.enabled).toBe(false);
    });
    
    test('Reverse 활성화 (use_entry_opposite)', () => {
      const draft: StrategyDraft = {
        name: 'Test',
        description: '',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'number', value: 100 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: true, mode: 'use_entry_opposite' },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      expect(json.reverse.enabled).toBe(true);
      if ('mode' in json.reverse) {
        expect(json.reverse.mode).toBe('use_entry_opposite');
      }
    });
  });
  
  describe('결정성 테스트', () => {
    test('동일 Draft → 동일 JSON', () => {
      const draft1: StrategyDraft = {
        name: 'Test Strategy',
        description: 'Test',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'number', value: 100 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      // 동일한 Draft 복사본
      const draft2: StrategyDraft = JSON.parse(JSON.stringify(draft1));
      
      const json1 = draftToStrategyJSON(draft1);
      const json2 = draftToStrategyJSON(draft2);
      
      expect(JSON.stringify(json1)).toBe(JSON.stringify(json2));
    });
    
    test('동일 Draft → 동일 Canonical JSON', () => {
      const draft: StrategyDraft = {
        name: 'Test Strategy',
        description: 'Test',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'number', value: 100 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json1 = draftToStrategyJSON(draft);
      const json2 = draftToStrategyJSON(JSON.parse(JSON.stringify(draft)));
      
      const canonical1 = canonicalizeStrategyJSON(json1);
      const canonical2 = canonicalizeStrategyJSON(json2);
      
      expect(canonical1).toBe(canonical2);
    });
    
    test('동일 Draft → 동일 strategy_hash', async () => {
      const draft: StrategyDraft = {
        name: 'Test Strategy',
        description: 'Test',
        indicators: [
          { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'indicator', value: 'ema_1' },
                operator: '>',
                right: { type: 'number', value: 100 }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json1 = draftToStrategyJSON(draft);
      const json2 = draftToStrategyJSON(JSON.parse(JSON.stringify(draft)));
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      expect(hash1).toBe(hash2);
      expect(hash1.length).toBe(64); // SHA-256 hex string
    });
  });
  
  describe('OHLCV 조건 변환 테스트', () => {
    test('OHLCV (price) 조건이 올바르게 변환됨', () => {
      const draft: StrategyDraft = {
        name: 'OHLCV Strategy',
        description: 'Close > EMA 조건 테스트',
        indicators: [
          { id: 'ema_20', type: 'ema', params: { source: 'close', period: 20 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'price', value: 'close' },
                operator: '>',
                right: { type: 'indicator', value: 'ema_20' }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json = draftToStrategyJSON(draft);
      
      // OHLCV 조건이 올바르게 변환되었는지 확인
      expect(json.entry.long.and.length).toBe(1);
      const condition = json.entry.long.and[0];
      
      // left가 price 타입으로 변환되었는지 확인
      expect('price' in condition.left).toBe(true);
      if ('price' in condition.left) {
        expect(condition.left.price).toBe('close');
      }
      
      // right가 ref 타입으로 변환되었는지 확인
      expect('ref' in condition.right).toBe(true);
      if ('ref' in condition.right) {
        expect(condition.right.ref).toBe('ema_20');
      }
      
      expect(condition.op).toBe('>');
    });
    
    test('모든 OHLCV 필드가 올바르게 변환됨', () => {
      const ohlcvFields = ['open', 'high', 'low', 'close', 'volume'];
      
      for (const field of ohlcvFields) {
        const draft: StrategyDraft = {
          name: `${field.toUpperCase()} Strategy`,
          description: `${field} 조건 테스트`,
          indicators: [],
          entry: {
            long: {
              conditions: [
                {
                  tempId: '1',
                  left: { type: 'price', value: field },
                  operator: '>',
                  right: { type: 'number', value: 1000 }
                }
              ]
            },
            short: { conditions: [] }
          },
          stopLoss: { type: 'fixed_percent', percent: 2 },
          reverse: { enabled: false },
          hook: { enabled: false }
        };
        
        const json = draftToStrategyJSON(draft);
        const condition = json.entry.long.and[0];
        
        expect('price' in condition.left).toBe(true);
        if ('price' in condition.left) {
          expect(condition.left.price).toBe(field);
        }
      }
    });
    
    test('OHLCV 조건이 포함된 전략의 hash가 일관되게 생성됨', async () => {
      const draft: StrategyDraft = {
        name: 'Volume Filter Strategy',
        description: 'Volume > 평균 조건',
        indicators: [
          { id: 'sma_volume', type: 'sma', params: { source: 'volume', period: 20 } }
        ],
        entry: {
          long: {
            conditions: [
              {
                tempId: '1',
                left: { type: 'price', value: 'volume' },
                operator: '>',
                right: { type: 'indicator', value: 'sma_volume' }
              }
            ]
          },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const json1 = draftToStrategyJSON(draft);
      const json2 = draftToStrategyJSON(JSON.parse(JSON.stringify(draft)));
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      expect(hash1).toBe(hash2);
    });
  });
});

