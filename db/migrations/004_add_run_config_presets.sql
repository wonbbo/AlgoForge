-- 004_add_run_config_presets.sql
-- Run 수행 옵션 프리셋 테이블 추가

-- 1. run_config_presets 테이블 생성
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

-- 2. runs 테이블에 preset_id 컬럼 추가
ALTER TABLE runs ADD COLUMN preset_id INTEGER REFERENCES run_config_presets(preset_id);

-- 3. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_runs_preset ON runs(preset_id);
CREATE INDEX IF NOT EXISTS idx_presets_default ON run_config_presets(is_default);

-- 4. 기본 프리셋 3개 삽입
-- 현재 시각 (Unix timestamp)
-- SQLite에서는 strftime('%s', 'now')로 현재 Unix timestamp 가져옴

-- 기본 프리셋 (2% 리스크, 1.5 R:R)
INSERT INTO run_config_presets (
    name,
    description,
    initial_balance,
    risk_percent,
    risk_reward_ratio,
    rebalance_interval,
    is_default,
    created_at,
    updated_at
) VALUES (
    '기본',
    '표준 리스크 관리 설정 (2% 리스크, 1.5 R:R)',
    1000.0,
    0.02,
    1.5,
    50,
    1,
    strftime('%s', 'now'),
    strftime('%s', 'now')
);

-- 보수적 프리셋 (1% 리스크, 2.0 R:R)
INSERT INTO run_config_presets (
    name,
    description,
    initial_balance,
    risk_percent,
    risk_reward_ratio,
    rebalance_interval,
    is_default,
    created_at,
    updated_at
) VALUES (
    '보수적',
    '낮은 리스크, 높은 R:R (1% 리스크, 2.0 R:R)',
    1000.0,
    0.01,
    2.0,
    50,
    0,
    strftime('%s', 'now'),
    strftime('%s', 'now')
);

-- 공격적 프리셋 (3% 리스크, 1.5 R:R)
INSERT INTO run_config_presets (
    name,
    description,
    initial_balance,
    risk_percent,
    risk_reward_ratio,
    rebalance_interval,
    is_default,
    created_at,
    updated_at
) VALUES (
    '공격적',
    '높은 리스크, 표준 R:R (3% 리스크, 1.5 R:R)',
    1000.0,
    0.03,
    1.5,
    50,
    0,
    strftime('%s', 'now'),
    strftime('%s', 'now')
);
