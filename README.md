# StockLens

StockLens 是一個台股量化分析 Dashboard，整合股價資料蒐集、資料庫管理、量化因子計算與視覺化呈現。

本專案目前支援 30 檔台股與 ETF，抓取近 365 天歷史資料，並透過 Streamlit Dashboard 顯示市場概覽、因子排行、個股分析與股票比較。

## 專案功能

- 從 FinMind API 抓取台股每日股價
- 將資料清洗後寫入 PostgreSQL
- 計算量化因子：
  - 20 日報酬率
  - 60 日報酬率
  - 20 日波動率
  - 最大回撤
  - 成交量倍率
  - Health Score
  - K-means 分群
- 提供 Streamlit Dashboard 視覺化分析結果
- 支援資料品質檢查

## 專案架構

```text
StockLens/
├── stock_schema.sql        # PostgreSQL 資料表與 Views
├── stock_list.py           # 30 檔股票清單與產業分類
├── stock_etl.py            # ETL：抓資料、清洗、入庫、資料品質檢查
├── stock_factors.py        # 量化因子計算與 K-means 分群
├── app.py                  # Streamlit Dashboard 主頁
├── pages/                  # Dashboard 子頁
│   └── 4_股票比較.py
├── Dockerfile              # Dashboard app Docker 設定
├── docker-compose.yml      # PostgreSQL + Dashboard 一鍵啟動
├── docker-entrypoint.sh    # 容器啟動流程
├── requirements.txt        # Python 套件
├── .env.example            # 環境變數範本
└── .gitignore
```

## 快速開始

建議使用 Docker Compose 啟動完整系統。

### 1. Clone 專案

```bash
git clone https://github.com/JoannaLai909/StockLens.git
cd StockLens
```

### 2. 設定環境變數

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

> `FINMIND_TOKEN` 可留空。若遇到 API 速率限制，再申請 FinMind token。

### 3. 啟動系統

請先確認 Docker Desktop 已開啟。

```bash
docker compose up --build
```

系統會自動執行：

```text
啟動 PostgreSQL
初始化資料庫
抓取近 365 天股價資料
計算量化因子
啟動 Streamlit Dashboard
```

啟動完成後打開：

```text
http://localhost:8501
```

### 4. 停止系統

```text
Control + C
```

若要關閉 container：

```bash
docker compose down
```

## Dashboard 頁面

- 市場概覽
- 因子排行 Top 10
- 個股分析
- 股票比較

## 手動執行

若不使用 Docker Compose，可依序執行：

```bash
pip3 install -r requirements.txt

python3 stock_etl.py --init-db
python3 stock_etl.py
python3 stock_factors.py --cluster

streamlit run app.py
```

## 資料品質檢查

可使用以下指令檢查 `daily_prices` 資料品質：

```bash
python3 stock_etl.py --quality-check
```

目前檢查項目包含：

- 每檔股票資料筆數
- 資料起始日與結束日
- `close` 空值
- `volume` 空值
- 價格異常
- 成交量異常

目前測試結果：

```text
股票數量：30 檔
資料期間：2025-05-29 至 2026-05-28
daily_prices 總筆數：7285 筆
close 空值：0
volume 空值：0
價格異常：0
成交量異常：0
```

## 資料流程

```text
FinMind API
   ↓
stock_etl.py
   ↓
daily_prices
   ↓
stock_factors.py
   ↓
factor_scores
   ↓
SQL Views
   ↓
Streamlit Dashboard
```

## 主要資料表

| 資料表 | 說明 |
|--------|------|
| `stocks` | 股票基本資料與產業分類 |
| `daily_prices` | 每日股價資料 |
| `factor_scores` | 量化因子、Health Score 與分群結果 |

## Views

| View | 說明 |
|------|------|
| `v_latest_factors` | 最新日期的股票因子與收盤價 |
| `v_top10_return_20d` | 近 20 日報酬率 Top 10 |
| `v_industry_avg` | 各產業平均因子表現 |

## 分工

| 成員 | 負責內容 |
|------|----------|
| A | 資料庫 schema、ETL、股票清單、資料品質檢查 |
| B | 量化因子、Health Score、K-means 分群 |
| C | Streamlit Dashboard、互動圖表、Docker 整合 |

## 常見問題

| 狀況 | 處理方式 |
|------|----------|
| `docker` 找不到 | 請先安裝並開啟 Docker Desktop |
| `localhost:8501` 打不開 | 確認 `docker compose up` 還在執行 |
| 第一次啟動很久 | 系統會抓 30 檔股票、近 365 天資料，屬於正常現象 |
| 資料庫連不上 | 確認 `.env` 的帳號、密碼與 port 設定正確 |
| port 5433 被佔用 | 停止舊的 PostgreSQL container，例如 `docker stop stockdb` |
| Dashboard 沒資料 | 確認 ETL 與因子計算有成功執行 |