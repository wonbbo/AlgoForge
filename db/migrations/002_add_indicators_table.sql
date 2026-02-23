-- 지표 관리 테이블 추가
-- 내장 지표 메타데이터와 커스텀 지표를 관리

CREATE TABLE IF NOT EXISTS indicators (
    indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                     -- 지표 이름 (예: "EMA")
    type TEXT NOT NULL UNIQUE,              -- 지표 타입 (고유 ID, 예: "ema")
    description TEXT,                       -- 지표 설명
    category TEXT NOT NULL,                 -- 카테고리: 'trend', 'momentum', 'volatility', 'volume'
    implementation_type TEXT NOT NULL,      -- 'builtin' 또는 'custom'
    code TEXT,                              -- 커스텀 지표의 Python 코드 (builtin은 NULL)
    params_schema TEXT,                     -- JSON: 파라미터 스키마
    output_fields TEXT NOT NULL,            -- JSON: 출력 필드 목록 ['main'] or ['main', 'signal', 'histogram']
    created_at INTEGER NOT NULL,            -- 생성 시간 (Unix timestamp)
    updated_at INTEGER NOT NULL             -- 수정 시간 (Unix timestamp)
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_indicators_type ON indicators(type);
CREATE INDEX IF NOT EXISTS idx_indicators_category ON indicators(category);
CREATE INDEX IF NOT EXISTS idx_indicators_implementation ON indicators(implementation_type);

-- 기본 내장 지표 데이터 삽입
INSERT INTO indicators (name, type, description, category, implementation_type, code, params_schema, output_fields, created_at, updated_at)
VALUES 
    ('EMA', 'ema', 'Exponential Moving Average - 지수 이동 평균', 'trend', 'builtin', NULL, 
     '{"source": "close", "period": 20}', '["main"]', 
     strftime('%s', 'now'), strftime('%s', 'now')),
    
    ('SMA', 'sma', 'Simple Moving Average - 단순 이동 평균', 'trend', 'builtin', NULL,
     '{"source": "close", "period": 20}', '["main"]',
     strftime('%s', 'now'), strftime('%s', 'now')),
    
    ('RSI', 'rsi', 'Relative Strength Index - 상대 강도 지수', 'momentum', 'builtin', NULL,
     '{"source": "close", "period": 14}', '["main"]',
     strftime('%s', 'now'), strftime('%s', 'now')),
    
    ('ATR', 'atr', 'Average True Range - 평균 진폭', 'volatility', 'builtin', NULL,
     '{"period": 14}', '["main"]',
     strftime('%s', 'now'), strftime('%s', 'now')),
    
    ('ADX', 'adx', 'Average Directional Index - 평균 방향성 지수', 'trend', 'builtin', NULL,
     '{"period": 14}', '["main"]',
     strftime('%s', 'now'), strftime('%s', 'now'));

