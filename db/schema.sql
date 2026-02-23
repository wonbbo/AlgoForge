-- AlgoForge Database Schema v1.1
-- Updated: 2025-12-15
-- Changes:
--   - Added chart_config field to indicators table
--   - All migrations integrated into base schema

-- WAL mode 활성화
PRAGMA journal_mode=WAL;

-- indicators 테이블 (내장/커스텀 지표 메타데이터)
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
    chart_config TEXT,                      -- JSON: 차트 설정 (output_field -> {chart_name, type, properties})
    created_at INTEGER NOT NULL,            -- 생성 시간 (Unix timestamp)
    updated_at INTEGER NOT NULL             -- 수정 시간 (Unix timestamp)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_indicators_type ON indicators(type);
CREATE INDEX IF NOT EXISTS idx_indicators_category ON indicators(category);
CREATE INDEX IF NOT EXISTS idx_indicators_implementation ON indicators(implementation_type);

-- 내장 지표 기본 데이터 삽입 (중복 방지를 위해 OR IGNORE 사용)
INSERT OR IGNORE INTO indicators (
    name, type, description, category, implementation_type, code, params_schema, output_fields, created_at, updated_at
) VALUES
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

-- datasets 테이블
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    timeframe TEXT NOT NULL DEFAULT '5m',
    dataset_hash TEXT NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    bars_count INTEGER NOT NULL,
    start_timestamp INTEGER NOT NULL,
    end_timestamp INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

-- strategies 테이블
CREATE TABLE IF NOT EXISTS strategies (
    strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    strategy_hash TEXT NOT NULL,
    definition TEXT NOT NULL,  -- JSON
    created_at INTEGER NOT NULL
);

-- runs 테이블
CREATE TABLE IF NOT EXISTS runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    strategy_id INTEGER NOT NULL,
    status TEXT NOT NULL,  -- PENDING, RUNNING, COMPLETED, FAILED
    engine_version TEXT NOT NULL,
    initial_balance REAL NOT NULL,
    started_at INTEGER,
    completed_at INTEGER,
    run_artifacts TEXT,  -- JSON (warnings 등)
    progress_percent REAL DEFAULT 0,  -- 진행률 (0~100)
    processed_bars INTEGER DEFAULT 0,  -- 처리된 봉 개수
    total_bars INTEGER DEFAULT 0,  -- 전체 봉 개수
    preset_id INTEGER,  -- Run 수행 옵션 프리셋 ID
    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id) ON DELETE RESTRICT,
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id) ON DELETE RESTRICT,
    FOREIGN KEY (preset_id) REFERENCES run_config_presets(preset_id) ON DELETE RESTRICT
);

-- trades 테이블
CREATE TABLE IF NOT EXISTS trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    direction TEXT NOT NULL,  -- LONG, SHORT
    entry_timestamp INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    position_size REAL NOT NULL,
    initial_risk REAL NOT NULL,
    stop_loss REAL NOT NULL,
    take_profit_1 REAL NOT NULL,
    leverage REAL NOT NULL DEFAULT 1.0, -- 사용된 레버리지
    is_closed INTEGER NOT NULL DEFAULT 0,
    total_pnl REAL,
    balance_at_entry REAL NOT NULL DEFAULT 0.0,  -- 진입 시점의 잔고 (리스크 제한 계산용)
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

-- trade_legs 테이블
CREATE TABLE IF NOT EXISTS trade_legs (
    leg_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,
    exit_type TEXT NOT NULL,  -- SL, TP1, BE, REVERSE
    exit_timestamp INTEGER NOT NULL,
    exit_price REAL NOT NULL,
    qty_ratio REAL NOT NULL,
    pnl REAL NOT NULL,
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
);

-- metrics 테이블
CREATE TABLE IF NOT EXISTS metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL UNIQUE,
    trades_count INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    tp1_hit_rate REAL NOT NULL,
    be_exit_rate REAL NOT NULL,
    total_pnl REAL NOT NULL,
    average_pnl REAL NOT NULL,
    profit_factor REAL NOT NULL,
    max_drawdown REAL NOT NULL,
    max_consecutive_wins INTEGER NOT NULL,
    max_consecutive_losses INTEGER NOT NULL,
    expectancy REAL NOT NULL,
    score REAL NOT NULL,
    grade TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

-- leverage_brackets 테이블
CREATE TABLE IF NOT EXISTS leverage_brackets (
    bracket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bracket_min REAL NOT NULL,
    bracket_max REAL NOT NULL,
    max_leverage REAL NOT NULL,
    m_margin_rate REAL NOT NULL,
    m_amount REAL NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE(bracket_min, bracket_max)
);

-- 레버리지 기본 데이터 삽입 (테스트 및 기본 동작용)
INSERT OR IGNORE INTO leverage_brackets (
    bracket_min, bracket_max, max_leverage, m_margin_rate, m_amount, created_at
) VALUES
    (0, 10000, 75, 0.005, 0, strftime('%s','now')),
    (10000, 200000, 75, 0.005, 0, strftime('%s','now')),
    (200000, 1000000000, 25, 0.01, 0, strftime('%s','now'));

-- run_config_presets 테이블
CREATE TABLE IF NOT EXISTS run_config_presets (
    preset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    initial_balance REAL NOT NULL DEFAULT 1000.0,
    risk_percent REAL NOT NULL DEFAULT 0.02,
    risk_reward_ratio REAL NOT NULL DEFAULT 1.5,
    rebalance_interval INTEGER NOT NULL DEFAULT 50,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- 기본 프리셋 데이터 삽입 (중복 방지를 위해 OR IGNORE 사용)
INSERT OR IGNORE INTO run_config_presets (
    name, description, initial_balance, risk_percent, risk_reward_ratio, 
    rebalance_interval, is_default, created_at, updated_at
) VALUES
    ('기본', '표준 리스크 관리 설정 (2% 리스크, 1.5 R:R)', 1000.0, 0.02, 1.5, 50, 1,
     strftime('%s', 'now'), strftime('%s', 'now')),
    ('보수적', '낮은 리스크, 높은 R:R (1% 리스크, 2.0 R:R)', 1000.0, 0.01, 2.0, 50, 0,
     strftime('%s', 'now'), strftime('%s', 'now')),
    ('공격적', '높은 리스크, 표준 R:R (3% 리스크, 1.5 R:R)', 1000.0, 0.03, 1.5, 50, 0,
     strftime('%s', 'now'), strftime('%s', 'now'));

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_runs_dataset ON runs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_runs_strategy ON runs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_runs_preset ON runs(preset_id);
CREATE INDEX IF NOT EXISTS idx_trades_run ON trades(run_id);
CREATE INDEX IF NOT EXISTS idx_trade_legs_trade ON trade_legs(trade_id);
CREATE INDEX IF NOT EXISTS idx_leverage_brackets_min ON leverage_brackets(bracket_min);
CREATE INDEX IF NOT EXISTS idx_presets_default ON run_config_presets(is_default);

