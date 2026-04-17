-- datasets 테이블에 symbol, market_type 컬럼 추가
-- 바이낸스 자동 데이터 수집 기능을 위한 메타데이터 확장

ALTER TABLE datasets ADD COLUMN symbol TEXT NOT NULL DEFAULT 'XRPUSDT';
ALTER TABLE datasets ADD COLUMN market_type TEXT NOT NULL DEFAULT 'futures_um';

-- 기존 데이터는 XRPUSDT / USDT-M 선물로 백필 (DEFAULT 값으로 이미 채워짐)

-- (symbol, market_type, timeframe) 조합 조회 최적화 인덱스
CREATE INDEX IF NOT EXISTS idx_datasets_symbol_market_tf
    ON datasets(symbol, market_type, timeframe);
