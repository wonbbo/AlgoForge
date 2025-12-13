-- 003_add_balance_at_entry.sql
-- trades 테이블에 balance_at_entry 컬럼 추가

-- balance_at_entry 컬럼 추가 (진입 시점의 잔고)
ALTER TABLE trades ADD COLUMN balance_at_entry REAL;

-- 기존 데이터를 위한 역계산
-- balance_at_entry = (position_size * initial_risk) / 0.02
UPDATE trades
SET balance_at_entry = (position_size * initial_risk) / 0.02
WHERE balance_at_entry IS NULL;

-- 새로운 trade는 NOT NULL이어야 하지만, 기존 데이터 때문에 일단 NULL 허용
-- 추후 모든 데이터가 채워지면 NOT NULL 제약 추가 가능

