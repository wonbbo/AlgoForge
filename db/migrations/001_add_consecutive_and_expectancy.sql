-- Migration: Add consecutive wins/losses and expectancy to metrics table
-- Date: 2025-12-13
-- Description: 최대 연속 수익/손실 거래수와 Trading Edge(Expectancy) 필드 추가

-- 1. 기존 metrics 테이블 백업
CREATE TABLE IF NOT EXISTS metrics_backup AS SELECT * FROM metrics;

-- 2. 새 컬럼 추가
ALTER TABLE metrics ADD COLUMN max_consecutive_wins INTEGER NOT NULL DEFAULT 0;
ALTER TABLE metrics ADD COLUMN max_consecutive_losses INTEGER NOT NULL DEFAULT 0;
ALTER TABLE metrics ADD COLUMN expectancy REAL NOT NULL DEFAULT 0.0;

-- 3. 기존 데이터가 있다면 기본값으로 설정됨
-- 주의: 기존 Run의 정확한 값을 얻으려면 재계산이 필요함
-- (별도 스크립트로 처리 가능)

-- Migration complete

