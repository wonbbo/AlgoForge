-- Migration 006: trades 테이블에 leverage 컬럼 추가
-- 각 거래에서 사용한 레버리지 정보를 기록

-- leverage 컬럼 추가 (기본값 1.0 = 레버리지 없음)
ALTER TABLE trades ADD COLUMN leverage REAL NOT NULL DEFAULT 1.0;
