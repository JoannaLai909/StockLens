# 成員 A：資料工程 Day 1-3

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `schema.sql` | PostgreSQL 建表 SQL（stocks / daily_prices / factor_scores + Views） |
| `stock_list.py` | 10 支股票清單與產業分類 |
| `etl.py` | FinMind ETL：抓股價、清洗、入庫 |
| `requirements.txt` | Python 套件 |

---

## 快速開始

### 1. 安裝套件
```bash
pip install -r requirements.txt
```

### 2. 啟動 PostgreSQL（本機沒裝可先用 Docker）
```bash
docker run -d \
  --name stockdb \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=stockdb \
  -p 5432:5432 \
  postgres:15
```
> 💡 初學者也可先用 SQLite，Day 8 再換 PostgreSQL（參考下方 SQLite 替代說明）

### 3. 設定環境變數（或直接改 etl.py 裡的 DB_CONFIG）
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=stockdb
export DB_USER=postgres
export DB_PASSWORD=postgres

# FinMind token（免費版可不設，有 token 速率上限較高）
export FINMIND_TOKEN=你的token
```

### 4. 初始化資料庫（建表 + 寫入股票清單）
```bash
python etl.py --init-db
```

### 5. 執行 ETL
```bash
# 抓所有 10 支股票，近 90 天
python etl.py

# 抓近 180 天
python etl.py --days 180

# 只抓台積電（測試用）
python etl.py --stock 2330
```

### 6. 驗證資料
```sql
-- psql 確認入庫
SELECT stock_id, COUNT(*) as days, MIN(date), MAX(date)
FROM daily_prices
GROUP BY stock_id
ORDER BY stock_id;
```

---

## 資料表說明

### `stocks`
基本資料：股票代號、公司名稱、產業分類（semiconductor / financial / etf / other）

### `daily_prices`
日 K 資料：open / high / low / close / volume / trade_value

### `factor_scores`
由**成員 B** 計算後寫入：return_20d / return_60d / volatility_20d / max_drawdown / volume_ratio / health_score / cluster_label

### Views（給成員 C 的 Dashboard 直接用）
| View | 說明 |
|------|------|
| `v_latest_factors` | 最新日期的所有股票因子 |
| `v_top10_return_20d` | 近 20 日報酬率 Top 10 |
| `v_industry_avg` | 各產業平均因子表現 |

---

## 里程碑確認（Day 3）

```bash
# 跑這個查詢，看到資料代表 Day 3 完成 ✅
psql -U postgres -d stockdb -c "
  SELECT stock_id, COUNT(*) as rows FROM daily_prices GROUP BY stock_id;
"
```

---

## SQLite 替代方案（初學者）

若還沒裝 PostgreSQL，可先改用 SQLite：

1. 把 `etl.py` 裡的 `psycopg2` 換成 `sqlite3`（標準庫，不用安裝）
2. 連線改成 `conn = sqlite3.connect("stock.db")`
3. `execute_values` 改成 `executemany`
4. Day 8 再遷移到 PostgreSQL，schema 不用改太多
