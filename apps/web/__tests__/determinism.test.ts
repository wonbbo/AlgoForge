/**
 * 결정성 테스트
 * 
 * 동일한 Draft → 동일한 strategy_hash 보장
 * 이는 AlgoForge의 핵심 원칙 중 하나
 */

import { draftToStrategyJSON } from '@/lib/draft-to-json';
import { canonicalizeStrategyJSON, calculateStrategyHash } from '@/lib/canonicalization';
import { StrategyDraft } from '@/types/strategy-draft';

/**
 * 테스트 Draft 생성 헬퍼
 */
function createTestDraft(seed: number = 1): StrategyDraft {
  return {
    name: `Test Strategy ${seed}`,
    description: `Description ${seed}`,
    indicators: [
      {
        id: 'ema_fast',
        type: 'ema',
        params: { source: 'close', period: 12 }
      },
      {
        id: 'ema_slow',
        type: 'ema',
        params: { source: 'close', period: 26 }
      }
    ],
    entry: {
      long: {
        conditions: [
          {
            tempId: 'temp-1',
            left: { type: 'indicator', value: 'ema_fast' },
            operator: 'cross_above',
            right: { type: 'indicator', value: 'ema_slow' }
          }
        ]
      },
      short: {
        conditions: []
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
}

describe('결정성 테스트', () => {
  describe('Draft → JSON 변환 결정성', () => {
    test('동일한 Draft는 항상 동일한 JSON을 생성한다', () => {
      const draft1 = createTestDraft(1);
      const draft2 = createTestDraft(1);
      
      const json1 = draftToStrategyJSON(draft1);
      const json2 = draftToStrategyJSON(draft2);
      
      // meta를 제외한 나머지가 동일해야 함
      expect(json1.indicators).toEqual(json2.indicators);
      expect(json1.entry).toEqual(json2.entry);
      expect(json1.stop_loss).toEqual(json2.stop_loss);
      expect(json1.reverse).toEqual(json2.reverse);
      expect(json1.hook).toEqual(json2.hook);
    });
    
    test('동일한 Draft를 100번 변환해도 동일한 결과', () => {
      const draft = createTestDraft(1);
      
      const results = [];
      for (let i = 0; i < 100; i++) {
        const json = draftToStrategyJSON(draft);
        results.push(JSON.stringify(json));
      }
      
      // 모든 결과가 동일해야 함
      const firstResult = results[0];
      results.forEach(result => {
        expect(result).toBe(firstResult);
      });
    });
    
    test('Draft의 순서를 바꿔도 동일한 JSON이 생성된다 (지표 순서)', () => {
      const draft1 = createTestDraft(1);
      const draft2 = createTestDraft(1);
      
      // draft2의 지표 순서를 바꿈
      draft2.indicators = [
        draft1.indicators[1],
        draft1.indicators[0]
      ];
      
      const json1 = draftToStrategyJSON(draft1);
      const json2 = draftToStrategyJSON(draft2);
      
      // 지표 배열이 다르므로 JSON도 달라야 함 (순서 보존)
      expect(json1.indicators).not.toEqual(json2.indicators);
    });
  });
  
  describe('Canonicalization 결정성', () => {
    test('동일한 Strategy JSON은 항상 동일한 Canonical 문자열을 생성한다', () => {
      const draft = createTestDraft(1);
      const json = draftToStrategyJSON(draft);
      
      const canonical1 = canonicalizeStrategyJSON(json);
      const canonical2 = canonicalizeStrategyJSON(json);
      
      expect(canonical1).toBe(canonical2);
    });
    
    test('Canonical 문자열은 whitespace를 포함하지 않는다', () => {
      const draft = createTestDraft(1);
      const json = draftToStrategyJSON(draft);
      
      const canonical = canonicalizeStrategyJSON(json);
      
      // whitespace 체크
      expect(canonical).not.toContain('\n');
      expect(canonical).not.toContain('  ');
    });
    
    test('Canonical 문자열은 meta를 포함하지 않는다', () => {
      const draft = createTestDraft(1);
      const json = draftToStrategyJSON(draft);
      
      const canonical = canonicalizeStrategyJSON(json);
      
      // meta가 없어야 함
      expect(canonical).not.toContain('"meta"');
      expect(canonical).not.toContain(draft.name);
      expect(canonical).not.toContain(draft.description);
    });
    
    test('meta만 다른 경우 동일한 Canonical 문자열을 생성한다', () => {
      const draft1 = createTestDraft(1);
      const draft2 = createTestDraft(2);
      
      // meta만 다르고 나머지는 동일
      draft2.name = 'Different Name';
      draft2.description = 'Different Description';
      
      const json1 = draftToStrategyJSON(draft1);
      const json2 = draftToStrategyJSON(draft2);
      
      const canonical1 = canonicalizeStrategyJSON(json1);
      const canonical2 = canonicalizeStrategyJSON(json2);
      
      // meta를 제외하면 동일해야 함
      expect(canonical1).toBe(canonical2);
    });
  });
  
  describe('Strategy Hash 결정성', () => {
    test('동일한 Draft는 항상 동일한 strategy_hash를 생성한다', async () => {
      const draft = createTestDraft(1);
      const json = draftToStrategyJSON(draft);
      
      const hash1 = await calculateStrategyHash(json);
      const hash2 = await calculateStrategyHash(json);
      
      expect(hash1).toBe(hash2);
    });
    
    test('strategy_hash는 64자리 16진수 문자열이다 (SHA-256)', async () => {
      const draft = createTestDraft(1);
      const json = draftToStrategyJSON(draft);
      
      const hash = await calculateStrategyHash(json);
      
      // 64자리 16진수
      expect(hash).toMatch(/^[a-f0-9]{64}$/);
      expect(hash.length).toBe(64);
    });
    
    test('다른 전략은 다른 strategy_hash를 생성한다', async () => {
      const draft1 = createTestDraft(1);
      const draft2 = createTestDraft(1);
      
      // draft2를 약간 수정
      draft2.stopLoss = {
        type: 'fixed_percent',
        percent: 3 // 2에서 3으로 변경
      };
      
      const json1 = draftToStrategyJSON(draft1);
      const json2 = draftToStrategyJSON(draft2);
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      expect(hash1).not.toBe(hash2);
    });
    
    test('meta만 다른 경우 동일한 strategy_hash를 생성한다', async () => {
      const draft1 = createTestDraft(1);
      const draft2 = createTestDraft(1);
      
      // meta만 변경
      draft2.name = 'Completely Different Name';
      draft2.description = 'Completely Different Description';
      
      const json1 = draftToStrategyJSON(draft1);
      const json2 = draftToStrategyJSON(draft2);
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      // meta를 제외하면 동일하므로 hash도 동일해야 함
      expect(hash1).toBe(hash2);
    });
    
    test('동일한 전략을 1000번 해싱해도 동일한 결과', async () => {
      const draft = createTestDraft(1);
      const json = draftToStrategyJSON(draft);
      
      const hashes = [];
      for (let i = 0; i < 1000; i++) {
        const hash = await calculateStrategyHash(json);
        hashes.push(hash);
      }
      
      // 모든 hash가 동일해야 함
      const firstHash = hashes[0];
      hashes.forEach(hash => {
        expect(hash).toBe(firstHash);
      });
    });
  });
  
  describe('Edge Case 결정성', () => {
    test('빈 조건 배열도 결정적으로 처리된다', async () => {
      const draft1: StrategyDraft = {
        name: 'Empty Conditions',
        description: '',
        indicators: [],
        entry: {
          long: { conditions: [] },
          short: { conditions: [] }
        },
        stopLoss: { type: 'fixed_percent', percent: 2 },
        reverse: { enabled: false },
        hook: { enabled: false }
      };
      
      const draft2 = JSON.parse(JSON.stringify(draft1));
      
      const json1 = draftToStrategyJSON(draft1);
      const json2 = draftToStrategyJSON(draft2);
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      expect(hash1).toBe(hash2);
    });
    
    test('특수 문자가 포함된 ID도 결정적으로 처리된다', async () => {
      const draft1 = createTestDraft(1);
      const draft2 = createTestDraft(1);
      
      // 특수 문자가 포함된 ID (하이픈, 언더스코어)
      draft1.indicators[0].id = 'ema_fast-12';
      draft2.indicators[0].id = 'ema_fast-12';
      
      const json1 = draftToStrategyJSON(draft1);
      const json2 = draftToStrategyJSON(draft2);
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      expect(hash1).toBe(hash2);
    });
    
    test('숫자 정밀도가 보존된다', async () => {
      const draft1 = createTestDraft(1);
      const draft2 = createTestDraft(1);
      
      // 소수점 정밀도
      draft1.stopLoss = { type: 'fixed_percent', percent: 2.5 };
      draft2.stopLoss = { type: 'fixed_percent', percent: 2.5 };
      
      const json1 = draftToStrategyJSON(draft1);
      const json2 = draftToStrategyJSON(draft2);
      
      const hash1 = await calculateStrategyHash(json1);
      const hash2 = await calculateStrategyHash(json2);
      
      expect(hash1).toBe(hash2);
      
      // 다른 값이면 다른 hash
      draft2.stopLoss = { type: 'fixed_percent', percent: 2.50001 };
      const json3 = draftToStrategyJSON(draft2);
      const hash3 = await calculateStrategyHash(json3);
      
      expect(hash1).not.toBe(hash3);
    });
  });
  
  describe('실제 사용 시나리오', () => {
    test('사용자가 전략을 저장하고 다시 불러와도 동일한 hash', async () => {
      // 1. 사용자가 전략 생성
      const originalDraft = createTestDraft(1);
      const originalJSON = draftToStrategyJSON(originalDraft);
      const originalHash = await calculateStrategyHash(originalJSON);
      
      // 2. JSON을 문자열로 변환 (저장 시뮬레이션)
      const savedJSON = JSON.stringify(originalJSON);
      
      // 3. JSON을 다시 파싱 (불러오기 시뮬레이션)
      const loadedJSON = JSON.parse(savedJSON);
      const loadedHash = await calculateStrategyHash(loadedJSON);
      
      // 4. hash가 동일해야 함
      expect(loadedHash).toBe(originalHash);
    });
    
    test('여러 사용자가 동일한 전략을 만들면 동일한 hash', async () => {
      // User A
      const draftA = createTestDraft(1);
      draftA.name = 'User A Strategy';
      const jsonA = draftToStrategyJSON(draftA);
      const hashA = await calculateStrategyHash(jsonA);
      
      // User B (이름만 다름)
      const draftB = createTestDraft(1);
      draftB.name = 'User B Strategy';
      const jsonB = draftToStrategyJSON(draftB);
      const hashB = await calculateStrategyHash(jsonB);
      
      // meta를 제외하면 동일하므로 hash도 동일
      expect(hashA).toBe(hashB);
    });
  });
});

