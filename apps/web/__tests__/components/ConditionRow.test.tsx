/**
 * ConditionRow 컴포넌트 테스트
 * 
 * 조건 Row UI가 올바르게 렌더링되고 상호작용하는지 검증합니다.
 */

import { render, screen } from '@testing-library/react';
import { ConditionRow } from '@/app/strategies/builder/components/ConditionRow';
import { ConditionDraft, IndicatorDraft } from '@/types/strategy-draft';

describe('ConditionRow Component', () => {
  const mockIndicators: IndicatorDraft[] = [
    { id: 'ema_1', type: 'ema', params: { source: 'close', period: 12 } },
    { id: 'ema_2', type: 'ema', params: { source: 'close', period: 26 } }
  ];
  
  const mockCondition: ConditionDraft = {
    tempId: '1',
    left: { type: 'indicator', value: 'ema_1' },
    operator: '>',
    right: { type: 'indicator', value: 'ema_2' }
  };
  
  const mockOnChange = jest.fn();
  const mockOnRemove = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('컴포넌트가 올바르게 렌더링됨', () => {
    render(
      <ConditionRow
        condition={mockCondition}
        indicators={mockIndicators}
        onChange={mockOnChange}
        onRemove={mockOnRemove}
      />
    );
    
    // 기본적인 UI 요소가 렌더링되는지 확인 (좌변, 연산자, 우변 3개의 select)
    const comboboxes = screen.getAllByRole('combobox');
    expect(comboboxes).toHaveLength(3);
    
    // 삭제 버튼이 있는지 확인
    const deleteButton = screen.getByRole('button');
    expect(deleteButton).toBeInTheDocument();
  });
  
  test('지표 목록이 제공되면 올바르게 표시됨', () => {
    const { container } = render(
      <ConditionRow
        condition={mockCondition}
        indicators={mockIndicators}
        onChange={mockOnChange}
        onRemove={mockOnRemove}
      />
    );
    
    // 지표 옵션이 렌더링되는지 확인
    const options = container.querySelectorAll('option');
    const optionTexts = Array.from(options).map(opt => opt.textContent);
    
    // ema_1과 ema_2가 포함되어 있는지 확인
    expect(optionTexts.some(text => text?.includes('ema_1'))).toBe(true);
    expect(optionTexts.some(text => text?.includes('ema_2'))).toBe(true);
  });
  
  test('조건이 없는 경우에도 렌더링됨', () => {
    const emptyCondition: ConditionDraft = {
      tempId: '1',
      left: { type: 'indicator', value: '' },
      operator: '>',
      right: { type: 'indicator', value: '' }
    };
    
    render(
      <ConditionRow
        condition={emptyCondition}
        indicators={mockIndicators}
        onChange={mockOnChange}
        onRemove={mockOnRemove}
      />
    );
    
    // 빈 조건에도 select가 3개 렌더링되어야 함
    const comboboxes = screen.getAllByRole('combobox');
    expect(comboboxes).toHaveLength(3);
  });
  
  test('OHLCV 옵션이 표시됨', () => {
    const { container } = render(
      <ConditionRow
        condition={mockCondition}
        indicators={mockIndicators}
        onChange={mockOnChange}
        onRemove={mockOnRemove}
      />
    );
    
    // OHLCV 옵션이 렌더링되는지 확인
    const options = container.querySelectorAll('option');
    const optionTexts = Array.from(options).map(opt => opt.textContent);
    
    // OHLCV 옵션들이 포함되어 있는지 확인
    expect(optionTexts.some(text => text?.includes('Open'))).toBe(true);
    expect(optionTexts.some(text => text?.includes('High'))).toBe(true);
    expect(optionTexts.some(text => text?.includes('Low'))).toBe(true);
    expect(optionTexts.some(text => text?.includes('Close'))).toBe(true);
    expect(optionTexts.some(text => text?.includes('Volume'))).toBe(true);
  });
  
  test('OHLCV 값을 선택한 조건이 올바르게 렌더링됨', () => {
    const priceCondition: ConditionDraft = {
      tempId: '1',
      left: { type: 'price', value: 'close' },
      operator: '>',
      right: { type: 'indicator', value: 'ema_1' }
    };
    
    render(
      <ConditionRow
        condition={priceCondition}
        indicators={mockIndicators}
        onChange={mockOnChange}
        onRemove={mockOnRemove}
      />
    );
    
    // 좌변 select에 'close' 값이 선택되어 있는지 확인
    const comboboxes = screen.getAllByRole('combobox');
    expect(comboboxes[0]).toHaveValue('close');
  });
});

