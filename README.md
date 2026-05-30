# StockLens

StockLens 是一個台股量化分析平台，整合股價資料蒐集、PostgreSQL 資料庫、量化因子計算、FastAPI 後端與 Next.js 前端 Dashboard。

本專案目前支援 30 檔台股與 ETF，抓取近 365 天歷史資料，計算報酬率、波動率、最大回撤、成交量倍率、Health Score 與 K-means 分群，協助快速觀察股票表現與風險。

## 目前狀態

| 模組 | 狀態 |
| --- | --- |
| PostgreSQL 資料庫 | 已完成 |
| ETL 股價入庫 | 已完成 |
| 量化因子計算 | 已完成 |
| K-means 分群 | 已完成 |
| FastAPI 後端 | 已可提供資料 API |
| Next.js 首頁 Dashboard | 已完成基本版 |
| 因子排行頁 | 開發中 |
| 股票比較頁 | 開發中 |
| 資料健康頁 | 開發中 |

## 技術架構

```text
FinMind API
   ↓
ETL / Python
   ↓
PostgreSQL
   ↓
Factor Calculation / K-means
   ↓
FastAPI
   ↓
Next.js Dashboard
```

## 專案結構

```text
StockLens/
├── api/                    # FastAPI 後端
│   ├── main.py
│   ├── db.py
│   └── routers/
├── etl/                    # ETL 與量化因子計算
│   ├── stock_etl.py
│   ├── stock_factors.py
│   ├── stock_list.py
│   └── docker-entrypoint.sh
├── frontend/               # Next.js 前端
│   ├── src/app/
│   ├── src/components/
│   └── src/lib/
├── db/
│   └── stock_schema.sql    # PostgreSQL schema 與 views
├── archive/                # 舊 Streamlit 版本備份
├── docker-compose.yml
├── .env.example
└── README.md
```

## 快速開始

### 1. 設定環境變數

```bash
cp .env.example .env
open .env
```

`.env` 範例：

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=stockdb
DB_USER=stock_user
DB_PASSWORD=your_password_here
FINMIND_TOKEN=
```

`FINMIND_TOKEN` 可留空；若遇到 FinMind API 速率限制，再填入 token。

### 2. 啟動完整系統

請先確認 Docker Desktop 已開啟。

```bash
docker compose up --build
```

系統會依序啟動：

```text
PostgreSQL
ETL 股價資料入庫
量化因子與 K-means 分群
FastAPI 後端
Next.js 前端
```

啟動完成後打開：

```text
http://localhost:3000
```

API 健康檢查：

```text
http://localhost:8000/health
```

PostgreSQL 對外連線：

```text
localhost:5433
```

### 3. 停止系統

在執行中的終端機按：

```text
Control + C
```

若要關閉並清理 container：

```bash
docker compose down --remove-orphans
```

## 頁面規劃

| 路徑 | 頁面 | 狀態 |
| --- | --- | --- |
| `/` | 市場總覽 Dashboard | 已完成基本版 |
| `/rankings` | 因子排行 | 開發中 |
| `/stocks` | 個股分析清單 | 已完成基本版 |
| `/stocks/[id]` | 個股詳細分析 | 已完成基本版 |
| `/compare` | 股票比較 | 開發中 |
| `/health` | 資料健康 | 開發中 |

## API 路由

| API | 說明 |
| --- | --- |
| `/health` | API 狀態檢查 |
| `/api/market/overview` | 首頁 KPI 資料 |
| `/api/market/health-scatter` | 市場健康分布散點圖 |
| `/api/market/industry-avg` | 產業平均健康分數 |
| `/api/rankings` | 因子排行資料 |
| `/api/stocks` | 股票清單 |
| `/api/stocks/{stock_id}` | 單一股票最新因子資料 |
| `/api/stocks/{stock_id}/prices` | 單一股票股價走勢 |

## 資料表與 Views

| 名稱 | 說明 |
| --- | --- |
| `stocks` | 股票基本資料與產業分類 |
| `daily_prices` | 每日股價資料 |
| `factor_scores` | 量化因子、Health Score 與分群結果 |
| `v_latest_factors` | 最新日期的股票因子與收盤價 |
| `v_top10_return_20d` | 近 20 日報酬率 Top 10 |
| `v_industry_avg` | 各產業平均因子表現 |

## 手動檢查

### Python 語法檢查

```bash
PYTHONPYCACHEPREFIX=/private/tmp/python-cache python3 -m compileall -q api etl archive
```

### 前端 TypeScript 檢查

```bash
cd frontend
npm install
npx tsc --noEmit --incremental false
```

### 資料品質檢查

```bash
cd etl
python3 stock_etl.py --quality-check
```

## 常見問題

| 狀況 | 處理方式 |
| --- | --- |
| `localhost:3000` 打不開 | 確認 `stocklens-web` 已啟動 |
| `localhost:8000/health` 打不開 | 確認 `stocklens-api` 已啟動 |
| 資料庫連不上 | 確認 `.env` 的 DB 設定與 Docker container 狀態 |
| port 5433 被佔用 | 停止舊的 PostgreSQL container，例如 `docker stop stockdb` |
| 出現 orphan container | 執行 `docker compose down --remove-orphans` |
| Dashboard 沒資料 | 確認 `stocklens-etl` 已成功執行並 exited with code 0 |

## 分工

| 成員 | 負責內容 |
| --- | --- |
| A | 資料庫 schema、ETL、股票清單、資料品質檢查 |
| B | 量化因子、Health Score、K-means 分群 |
| C | Dashboard 前端、頁面視覺化、Docker 整合 |

## 備註

`archive/` 保留舊 Streamlit 版本，作為歷史參考；目前主要入口已改為 Next.js：

```text
http://localhost:3000
```
