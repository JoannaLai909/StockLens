-- ============================================================
-- 股票分析系統 Schema
-- 成員 A：資料工程 / Day 1-3
-- ============================================================

-- 若重建請先執行：
-- DROP TABLE IF EXISTS factor_scores, daily_prices, stocks CASCADE;

-- -------------------------------------------------------
-- 1. stocks：股票基本資料 + 產業分類
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS stocks (
    stock_id    VARCHAR(10)  PRIMARY KEY,          -- 股票代號，例如 2330
    name        VARCHAR(50)  NOT NULL,             -- 公司名稱
    category    VARCHAR(20)  NOT NULL,             -- 產業大類：semiconductor / financial / etf / other
    market      VARCHAR(10)  NOT NULL DEFAULT 'TSE', -- TSE（上市）/ OTC（上櫃）
    listed_date DATE,                              -- 上市日期
    created_at  TIMESTAMP    DEFAULT NOW()
);

-- -------------------------------------------------------
-- 2. daily_prices：每日股價（ETL 抓進來的原始資料）
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_prices (
    id          BIGSERIAL    PRIMARY KEY,
    stock_id    VARCHAR(10)  NOT NULL REFERENCES stocks(stock_id),
    date        DATE         NOT NULL,
    open        NUMERIC(10,2),
    high        NUMERIC(10,2),
    low         NUMERIC(10,2),
    close       NUMERIC(10,2) NOT NULL,
    volume      BIGINT,                            -- 成交股數
    trade_value BIGINT,                            -- 成交金額
    UNIQUE (stock_id, date)                        -- 避免重複入庫
);

CREATE INDEX IF NOT EXISTS idx_daily_prices_stock_date
    ON daily_prices (stock_id, date DESC);

-- -------------------------------------------------------
-- 3. factor_scores：成員 B 計算完因子後寫入這裡
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS factor_scores (
    id              BIGSERIAL    PRIMARY KEY,
    stock_id        VARCHAR(10)  NOT NULL REFERENCES stocks(stock_id),
    date            DATE         NOT NULL,          -- 計算基準日
    return_20d      NUMERIC(8,4),                   -- 近 20 日報酬率
    return_60d      NUMERIC(8,4),                   -- 近 60 日報酬率
    volatility_20d  NUMERIC(8,4),                   -- 20 日報酬率標準差（波動率）
    max_drawdown    NUMERIC(8,4),                   -- 最大回撤
    volume_ratio    NUMERIC(8,4),                   -- 成交量倍率（近5日均量 / 近20日均量）
    health_score    NUMERIC(5,2),                   -- 成員 B 的股票健康分數（0-100）
    cluster_label   SMALLINT,                       -- K-means 分群結果
    updated_at      TIMESTAMP    DEFAULT NOW(),
    UNIQUE (stock_id, date)
);

CREATE INDEX IF NOT EXISTS idx_factor_scores_stock_date
    ON factor_scores (stock_id, date DESC);

-- -------------------------------------------------------
-- 4. View：Dashboard 用的查詢介面（成員 C 可直接 SELECT）
-- -------------------------------------------------------

-- 最新一天的因子 + 股票基本資訊
CREATE OR REPLACE VIEW v_latest_factors AS
SELECT
    s.stock_id,
    s.name,
    s.category,
    f.date,
    dp.close                          AS latest_close,
    f.return_20d,
    f.return_60d,
    f.volatility_20d,
    f.max_drawdown,
    f.volume_ratio,
    f.health_score,
    f.cluster_label
FROM stocks s
JOIN factor_scores f
    ON s.stock_id = f.stock_id
JOIN daily_prices dp
    ON s.stock_id = dp.stock_id AND f.date = dp.date
WHERE f.date = (
    SELECT MAX(date) FROM factor_scores
);

-- Top 10 近 20 日報酬率排行
CREATE OR REPLACE VIEW v_top10_return_20d AS
SELECT
    stock_id, name, category,
    return_20d, health_score, latest_close
FROM v_latest_factors
ORDER BY return_20d DESC NULLS LAST
LIMIT 10;

-- 各產業平均因子表現
CREATE OR REPLACE VIEW v_industry_avg AS
SELECT
    s.category,
    COUNT(*)                          AS stock_count,
    ROUND(AVG(f.return_20d)::NUMERIC, 4)  AS avg_return_20d,
    ROUND(AVG(f.return_60d)::NUMERIC, 4)  AS avg_return_60d,
    ROUND(AVG(f.volatility_20d)::NUMERIC, 4) AS avg_volatility,
    ROUND(AVG(f.health_score)::NUMERIC, 2)   AS avg_health_score
FROM stocks s
JOIN factor_scores f ON s.stock_id = f.stock_id
WHERE f.date = (SELECT MAX(date) FROM factor_scores)
GROUP BY s.category;
