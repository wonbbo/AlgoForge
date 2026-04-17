-- 내장 지표 MACD, CCI 추가
-- - MACD: 다중 출력 지표 (main / signal / histogram)
-- - CCI : 단일 출력 지표 (main)
-- 중복 실행 시 안전하도록 INSERT OR IGNORE 사용

INSERT OR IGNORE INTO indicators (
    name,
    type,
    description,
    category,
    implementation_type,
    code,
    params_schema,
    output_fields,
    chart_config,
    created_at,
    updated_at
) VALUES
    (
        'MACD',
        'macd',
        'Moving Average Convergence Divergence - 이동평균 수렴 확산 지수',
        'momentum',
        'builtin',
        NULL,
        '{"source": "close", "fast_period": 12, "slow_period": 26, "signal_period": 9}',
        '["main", "signal", "histogram"]',
        -- MACD 전용 oscillator 차트에 3개 시리즈를 표시
        '{"main": {"chart_name": "macd", "type": "line", "properties": {"color": "#2962FF", "lineWidth": 2, "lineStyle": 0, "visible": true}}, "signal": {"chart_name": "macd", "type": "line", "properties": {"color": "#FF6D00", "lineWidth": 2, "lineStyle": 0, "visible": true}}, "histogram": {"chart_name": "macd", "type": "histogram", "properties": {"color": "#26A69A", "visible": true}}}',
        strftime('%s', 'now'),
        strftime('%s', 'now')
    ),
    (
        'CCI',
        'cci',
        'Commodity Channel Index - 상품 채널 지수',
        'momentum',
        'builtin',
        NULL,
        '{"period": 20, "constant": 0.015}',
        '["main"]',
        '{"main": {"chart_name": "cci", "type": "line", "properties": {"color": "#2962FF", "lineWidth": 2, "lineStyle": 0, "visible": true}}}',
        strftime('%s', 'now'),
        strftime('%s', 'now')
    );
