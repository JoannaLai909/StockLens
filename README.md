# StockLens

台股分析系統：抓取股價資料、計算量化因子，並用 Streamlit Dashboard 視覺化呈現。

## 專案架構

```text
StockLens/
├── stock_schema.sql        # PostgreSQL 資料表與 Views
├── stock_list.py           # 股票清單與產業分類
├── stock_etl.py            # 股價 ETL：抓資料、清洗、入庫
├── stock_factors.py        # 量化因子與 K-means 分群
├── app.py                  # Streamlit Dashboard 主頁
├── pages/                  # Dashboard 子頁
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── requirements.txt
└── .env.example
```

## 快速開始

建議使用 Docker Compose，一次啟動資料庫、ETL、因子計算與 Dashboard。

### 1. Clone 專案

```bash
git clone https://github.com/JoannaLai909/StockLens.git
cd StockLens
```

### 2. 設定環境變數

```bash
cp .env.example .env
open .env   # macOS；Windows 可用 notepad .env
```

### 3. 啟動完整系統

請先確認 Docker Desktop 已開啟。

```bash
docker compose up --build
```

第一次啟動會安裝套件、抓取股價資料並計算因子，時間會比較久。

啟動完成後打開：

```text
http://localhost:8501
```

### 4. 停止服務

```text
Control + C
```

若要完全關閉 container：

```bash
docker compose down
```

## Dashboard 功能

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

打開：

```text
http://localhost:8501
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
Views
   ↓
Streamlit Dashboard
```

## 主要資料表

| 資料表 | 說明 |
|--------|------|
| `stocks` | 股票基本資料 |
| `daily_prices` | 每日股價 |
| `factor_scores` | 量化因子與分群結果 |

## 常見問題

| 狀況 | 處理方式 |
|------|----------|
| `docker` 找不到 | 先安裝並開啟 Docker Desktop |
| `localhost:8501` 打不開 | 確認 `docker compose up` 還在執行 |
| 第一次啟動很久 | 正常，系統會抓資料並計算因子 |
| Dashboard 沒資料 | 確認 ETL 和因子計算有成功執行 |
| 資料庫連不上 | 確認 `.env` 的帳號、密碼與 port 設定一致 |
