-- run_datasets 정션 테이블: 하나의 run이 여러 dataset(타임프레임별)을 사용할 수 있도록 확장
-- 하위호환성:
--   - 기존 runs.dataset_id는 유지 (NULL 허용으로 전환)
--   - 기존 row는 (run_id, dataset_id, 'base')로 run_datasets에 복제됨

CREATE TABLE IF NOT EXISTS run_datasets (
    run_id INTEGER NOT NULL,
    dataset_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'base', 'htf_15m', 'htf_1h', 'htf_4h', 'htf_1d' 등 (자유 문자열이지만 규칙 권장)
    PRIMARY KEY (run_id, role),
    UNIQUE (run_id, dataset_id, role),
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_run_datasets_run ON run_datasets(run_id);
CREATE INDEX IF NOT EXISTS idx_run_datasets_dataset ON run_datasets(dataset_id);

-- 기존 runs row를 run_datasets에 'base'로 복제 (멱등)
INSERT OR IGNORE INTO run_datasets (run_id, dataset_id, role)
SELECT run_id, dataset_id, 'base' FROM runs WHERE dataset_id IS NOT NULL;
