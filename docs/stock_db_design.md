# 資料庫設計文檔

## 概覽

StockLens 使用 PostgreSQL 作為資料庫，共有 3 張資料表與 3 個 View。

```
stocks
  │
  ├──< daily_prices     （每日股價，由 ETL 寫入）
  │
  └──< factor_scores    （量化因子，由成員 B 寫入）
```

`daily_prices` 與 `factor_scores` 都透過 `stock_id` 外鍵關聯到 `stocks`，確保資料一致性。

---

## 資料表

### `stocks`

股票基本資料，是整個系統的主表，其他資料表都以此為基礎關聯。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `stock_id` | VARCHAR(10) | ✓ | 股票代號，主鍵，例如 `2330` |
| `name` | VARCHAR(50) | ✓ | 公司名稱 |
| `category` | VARCHAR(20) | ✓ | 產業分類：`semiconductor` / `financial` / `etf` / `other` |
| `market` | VARCHAR(10) | ✓ | 市場別：`TSE`（上市）/ `OTC`（上櫃），預設 `TSE` |
| `listed_date` | DATE | | 上市日期 |
| `created_at` | TIMESTAMP | | 建立時間，預設 `NOW()` |

---

### `daily_prices`

每日股價原始資料，由成員 A 的 ETL 從 FinMind API 抓取後寫入。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `id` | BIGSERIAL | ✓ | 自動遞增主鍵 |
| `stock_id` | VARCHAR(10) | ✓ | 外鍵，關聯 `stocks.stock_id` |
| `date` | DATE | ✓ | 交易日期 |
| `open` | NUMERIC(10,2) | | 開盤價 |
| `high` | NUMERIC(10,2) | | 最高價 |
| `low` | NUMERIC(10,2) | | 最低價 |
| `close` | NUMERIC(10,2) | ✓ | 收盤價 |
| `volume` | BIGINT | | 成交股數 |
| `trade_value` | BIGINT | | 成交金額（新台幣） |

**限制**
- `(stock_id, date)` 唯一約束，避免重複入庫
- ETL 使用 `ON CONFLICT DO UPDATE`，重跑不會產生重複資料

**索引**
```sql
idx_daily_prices_stock_date ON (stock_id, date DESC)
```
針對「查某支股票的近期股價」這個最常見的查詢模式做優化。

---

### `factor_scores`

量化因子，由成員 B 計算後寫入，供 Dashboard 與選股使用。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `id` | BIGSERIAL | ✓ | 自動遞增主鍵 |
| `stock_id` | VARCHAR(10) | ✓ | 外鍵，關聯 `stocks.stock_id` |
| `date` | DATE | ✓ | 因子計算基準日 |
| `return_20d` | NUMERIC(8,4) | | 近 20 日報酬率 |
| `return_60d` | NUMERIC(8,4) | | 近 60 日報酬率 |
| `volatility_20d` | NUMERIC(8,4) | | 近 20 日報酬率標準差（波動率） |
| `max_drawdown` | NUMERIC(8,4) | | 最大回撤 |
| `volume_ratio` | NUMERIC(8,4) | | 成交量倍率（近 5 日均量 ÷ 近 20 日均量） |
| `health_score` | NUMERIC(5,2) | | 股票健康分數，範圍 0–100 |
| `cluster_label` | SMALLINT | | K-means 分群結果 |
| `updated_at` | TIMESTAMP | | 最後更新時間，預設 `NOW()` |

**限制**
- `(stock_id, date)` 唯一約束

**索引**
```sql
idx_factor_scores_stock_date ON (stock_id, date DESC)
```

---

## Views

Views 是給成員 C Dashboard 直接使用的查詢介面，不需要自己寫複雜的 JOIN。

### `v_latest_factors`

取最新計算日期的所有股票因子，JOIN 了 `stocks`、`factor_scores`、`daily_prices`。

```sql
SELECT * FROM v_latest_factors;
```

回傳欄位：`stock_id`, `name`, `category`, `date`, `latest_close`, `return_20d`, `return_60d`, `volatility_20d`, `max_drawdown`, `volume_ratio`, `health_score`, `cluster_label`

---

### `v_top10_return_20d`

基於 `v_latest_factors`，取近 20 日報酬率最高的前 10 支股票。

```sql
SELECT * FROM v_top10_return_20d;
```

---

### `v_industry_avg`

各產業的平均因子表現，用於產業比較分析。

```sql
SELECT * FROM v_industry_avg;
```

回傳欄位：`category`, `stock_count`, `avg_return_20d`, `avg_return_60d`, `avg_volatility`, `avg_health_score`

---

## 資料流

```
FinMind API
    │
    ▼
etl.py（成員 A）→ stock_etl.py
    │  fetch → clean → upsert
    ▼
daily_prices
    │
    ▼
因子計算腳本（成員 B）
    │  讀取 daily_prices → 計算因子 → 寫入
    ▼
factor_scores
    │
    ▼
Views（v_latest_factors / v_top10_return_20d / v_industry_avg）
    │
    ▼
Dashboard（成員 C）
```

---

## 重建資料庫

```sql
-- 清除所有資料表（注意：資料會全部刪除）
DROP TABLE IF EXISTS factor_scores, daily_prices, stocks CASCADE;

-- 重新建立
-- 執行 stock_schema.sql 即可
```
