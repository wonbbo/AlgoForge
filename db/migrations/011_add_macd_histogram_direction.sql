-- MACD 내장 지표에 histogram_direction 출력 필드 추가
--
-- histogram_direction 값 정의 (이전 봉의 히스토그램과 비교):
--   +1 : 이전보다 증가 (상승 모멘텀 강화)
--   -1 : 이전보다 감소 (상승 모멘텀 약화 / 하락 모멘텀 강화)
--    0 : 이전과 동일 또는 첫 봉 (비교 불가)
--
-- 기존 DB에도 안전하게 적용되도록 UPDATE만 수행.
-- chart_config에는 동일 "macd" 패널에 숨김(visible=false)으로 등록하여
-- 전략 조건 평가에만 사용하고 차트에는 노출되지 않도록 함.

UPDATE indicators
SET
    output_fields = '["main", "signal", "histogram", "histogram_direction"]',
    chart_config  = '{"main": {"chart_name": "macd", "type": "line", "properties": {"color": "#2962FF", "lineWidth": 2, "lineStyle": 0, "visible": true}}, "signal": {"chart_name": "macd", "type": "line", "properties": {"color": "#FF6D00", "lineWidth": 2, "lineStyle": 0, "visible": true}}, "histogram": {"chart_name": "macd", "type": "histogram", "properties": {"color": "#26A69A", "visible": true}}, "histogram_direction": {"chart_name": "macd", "type": "line", "properties": {"color": "#9E9E9E", "lineWidth": 1, "lineStyle": 0, "visible": false}}}',
    updated_at    = strftime('%s', 'now')
WHERE type = 'macd'
  AND implementation_type = 'builtin';
