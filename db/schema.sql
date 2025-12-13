-- AlgoForge Database Schema v1.0

-- WAL mode 활성화
PRAGMA journal_mode=WAL;

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
    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id) ON DELETE RESTRICT,
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id) ON DELETE RESTRICT
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
    is_closed INTEGER NOT NULL DEFAULT 0,
    total_pnl REAL,
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

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_runs_dataset ON runs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_runs_strategy ON runs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_run ON trades(run_id);
CREATE INDEX IF NOT EXISTS idx_trade_legs_trade ON trade_legs(trade_id);

