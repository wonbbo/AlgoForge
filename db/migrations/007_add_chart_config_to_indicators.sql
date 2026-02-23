-- indicators 테이블에 chart_config 필드 추가
-- 각 output_field별로 차트 설정 정보 저장

-- chart_config 필드 추가
ALTER TABLE indicators ADD COLUMN chart_config TEXT;

-- 기존 지표에 대한 기본 chart_config 생성
-- 단일 출력 필드(main만)인 경우
-- 내장 지표: overlay 타입은 "main", oscillator 타입은 지표 타입명을 chart_name으로 사용
UPDATE indicators 
SET chart_config = CASE 
    WHEN type IN ('rsi', 'atr', 'adx', 'macd', 'stoch', 'cci', 'mfi', 'roc', 'willr') THEN
        '{"main": {"chart_name": "' || type || '", "type": "line", "properties": {"color": "#2962FF", "lineWidth": 2}}}'
    ELSE
        '{"main": {"chart_name": "main", "type": "line", "properties": {"color": "#2962FF", "lineWidth": 2}}}'
END
WHERE chart_config IS NULL AND output_fields = '["main"]';

