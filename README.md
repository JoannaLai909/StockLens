# StockLens

台股分析系統，透過 ETL 抓取股價資料、計算量化因子，並以 Dashboard 視覺化呈現。

## 專案架構

```
StockLens/
├── schema.sql        # PostgreSQL 建表 SQL
├── stock_list.py     # 股票清單與產業分類
├── etl.py            # FinMind ETL：抓股價、清洗、入庫
├── requirements.txt  # Python 套件
├── .env.example      # 環境變數範本
└── .gitignore
```

## 分工

| Branch | 成員 | 負責內容 |
|--------|------|----------|
| `feature/member-a-etl` | 成員 A | 資料工程：schema、ETL、股票清單 |
| `feature/member-b-factors` | 成員 B | 因子計算：報酬率、波動率、health score、K-means 分群 |
| `feature/member-c-dashboard` | 成員 C | Dashboard：資料視覺化 |

---

## 快速開始

### 1. Clone 並安裝套件

```bash
git clone https://github.com/JoannaLai909/StockLens.git
cd StockLens
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
cp .env.example .env
```

`.env` の預設值可以直接使用（DB 密碼對應下方 Docker 指令）。
`FINMIND_TOKEN` 是選填，免費版留空也能跑，有需要再到 [finmindtrade.com](https://finmindtrade.com) 註冊取得。

### 3. 啟動 PostgreSQL

```bash
docker run -d \
  --name stockdb \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=stockdb \
  -p 5432:5432 \
  postgres:15
```

### 4. 初始化資料庫

```bash
python etl.py --init-db
```

### 5. 執行 ETL

```bash
# 抓所有股票，近 90 天
python etl.py

# 抓近 180 天
python etl.py --days 180

# 只抓台積電（測試用）
python etl.py --stock 2330
```

---

## 資料表

| 資料表 | 說明 |
|--------|------|
| `stocks` | 股票基本資料（代號、名稱、產業） |
| `daily_prices` | 每日股價（由成員 A ETL 寫入） |
| `factor_scores` | 量化因子（由成員 B 計算後寫入） |

### Views（供成員 C Dashboard 使用）

| View | 說明 |
|------|------|
| `v_latest_factors` | 最新日期所有股票因子 |
| `v_top10_return_20d` | 近 20 日報酬率 Top 10 |
| `v_industry_avg` | 各產業平均因子表現 |

---

## 開發流程

各成員在自己的 branch 開發，完成後開 PR 合併回 `main`。

```bash
# 切到自己的 branch
git checkout feature/member-b-factors

# 開發完後 push
git push origin feature/member-b-factors

# 到 GitHub 開 Pull Request → main
```
