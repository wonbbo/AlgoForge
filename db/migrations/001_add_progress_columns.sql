-- Migration: Add progress tracking columns to runs table
-- Date: 2025-12-13

-- 진행률 추적을 위한 컬럼 추가
ALTER TABLE runs ADD COLUMN progress_percent REAL DEFAULT 0;
ALTER TABLE runs ADD COLUMN processed_bars INTEGER DEFAULT 0;
ALTER TABLE runs ADD COLUMN total_bars INTEGER DEFAULT 0;

