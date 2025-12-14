-- 005: trades 테이블에 balance_at_entry 컬럼 추가
-- balance_at_entry: 진입 시점의 잔고 (리스크 제한 계산용)

ALTER TABLE trades ADD COLUMN balance_at_entry REAL NOT NULL DEFAULT 0.0;
