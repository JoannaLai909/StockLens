# StockLens

台股分析系統，透過 ETL 抓取股價資料、計算量化因子，並以 Dashboard 視覺化呈現。

## 專案架構

```
StockLens/
├── stock_schema.sql  # PostgreSQL 建表 SQL（資料表 + Views）
├── stock_list.py     # 股票清單與產業分類
├── stock_etl.py      # FinMind ETL：抓股價、清洗、入庫
├── requirements.txt  # Python 套件
├── .env.example      # 環境變數範本
├── .gitignore
└── docs/
    └── stock_db_design.md  # 資料庫設計文檔
```

## 分工

| Branch | 成員 | 負責內容 |
|--------|------|----------|
| `feature/member-a-etl` | 成員 A | 資料工程：schema、ETL、股票清單 |
| `feature/member-b-factors` | 成員 B | 因子計算：報酬率、波動率、health score、K-means 分群 |
| `feature/member-c-dashboard` | 成員 C | Dashboard：資料視覺化 |

---

## 快速開始

> macOS 請用 `pip3` / `python3`；Windows / Linux 用 `pip` / `python` 即可。

### 前置條件：安裝 Docker Desktop

本專案使用 Docker 運行 PostgreSQL，請先確認已安裝 Docker Desktop：

- 下載：[https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
- 安裝完成後**開啟 Docker Desktop 並保持運行**，之後每次執行 ETL 前都需要確認 Docker Desktop 是開著的

確認安裝成功：

```bash
docker --version
# 預期看到類似：Docker version 24.x.x
```

### 1. Clone 並安裝套件 (路徑需自行調整)

```bash
git clone https://github.com/JoannaLai909/StockLens.git
cd stockLens
pip3 install -r requirements.txt
```

### 2. 設定環境變數

```bash
cp .env.example .env
open .env   # macOS；Windows 用 notepad .env
```

填入以下內容（存檔後關閉）：

```
DB_HOST=localhost
DB_PORT=5433
DB_NAME=stockdb
DB_USER=stock_user
DB_PASSWORD=你的密碼
FINMIND_TOKEN=
```

> `FINMIND_TOKEN` 選填，免費版留空也能跑；遇到速率限制再到 [finmindtrade.com](https://finmindtrade.com) 註冊取得。

### 3. 啟動 PostgreSQL（只需執行一次）

```bash
docker run -d \
  --name stockdb \
  -e POSTGRES_USER=stock_user \
  -e POSTGRES_PASSWORD=你的密碼 \
  -e POSTGRES_DB=stockdb \
  -p 5433:5432 \
  postgres:15
```

> `POSTGRES_USER` 與 `POSTGRES_PASSWORD` 必須和 `.env` 裡的 `DB_USER` / `DB_PASSWORD` 一致。  
> **這個指令只跑一次。** 之後重開電腦用 `docker start stockdb` 啟動，不要再跑 `docker run`。

確認 container 有跑起來：

```bash
docker ps
# 預期看到 STATUS 為 Up，PORTS 為 0.0.0.0:5433->5432/tcp
```

### 4. 初始化資料庫

```bash
python3 stock_etl.py --init-db
```

成功 log：

```
初始化資料庫 ... schema.sql 執行完成
stocks 表已寫入 10 筆
初始化完成
```

### 5. 執行 ETL

```bash
# 抓所有股票（近 90 天）
python3 stock_etl.py

# 近 180 天
python3 stock_etl.py --days 180

# 只抓單一股票（測試用）
python3 stock_etl.py --stock 2330
```

### 6. 驗證資料入庫

```bash
docker exec -it stockdb psql -U stock_user -d stockdb -c \
  "SELECT stock_id, COUNT(*) AS days, MIN(date) AS start, MAX(date) AS end \
   FROM daily_prices \
   GROUP BY stock_id \
   ORDER BY stock_id;"
```

預期看到 10 支股票各有對應筆數，代表 ETL 成功 ✅

---

## 啟動 Dashboard 前端

目前 `main` 已整合 Streamlit Dashboard 與 Docker Compose。若只想快速開啟前端展示，建議直接使用 Docker Compose，會自動啟動 PostgreSQL、初始化資料庫、執行 ETL、計算因子，最後開啟 Dashboard。

### 1. 確認 Docker Desktop 已開啟

```bash
docker --version
```

### 2. 設定環境變數

```bash
cp .env.example .env
open .env   # macOS；Windows 用 notepad .env
```

`.env` 可先使用以下設定：

```
DB_HOST=localhost
DB_PORT=5433
DB_NAME=stockdb
DB_USER=stock_user
DB_PASSWORD=stock_password
FINMIND_TOKEN=
```

### 3. 啟動前端與資料服務

```bash
docker compose up --build
```

第一次啟動會下載映像檔、安裝套件、抓取股價資料並計算因子，時間會比較久。看到終端機出現 Dashboard 啟動訊息後，打開瀏覽器：

```text
http://localhost:8501
```

### 4. 停止服務

在執行 `docker compose up --build` 的終端機按：

```text
Control + C
```

若要完全關閉並移除 container：

```bash
docker compose down
```

---

## 重開電腦後的流程

Container 重開後會停止，每次需先啟動再跑 ETL：

```bash
# 1. 啟動 container
docker start stockdb

# 2. 確認有跑起來
docker ps

# 3. 更新資料（如需要）
python3 stock_etl.py
```

---

## 資料表

| 資料表 | 說明 |
|--------|------|
| `stocks` | 股票基本資料（代號、名稱、產業） |
| `daily_prices` | 每日股價，由成員 A ETL 寫入 |
| `factor_scores` | 量化因子，由成員 B 計算後寫入 |

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

# 到 GitHub 開 Pull Request -> main
```

---

## 常見問題

| 狀況 | 說明 |
|------|------|
| `pip` 找不到指令 | macOS 請用 `pip3` |
| `python` 找不到指令 | macOS 請用 `python3` |
| `docker` 找不到指令 | Docker Desktop 尚未安裝，請先至官網下載安裝 |
| 連不上資料庫（剛開機） | 確認 Docker Desktop 已開啟，再執行 `docker start stockdb` |
| port 5432 被佔用 | 改用 5433，`.env` 的 `DB_PORT` 與 `docker run` 的 `-p` 都要改 |
| `docker run` 只執行一次 | 之後重開電腦用 `docker start stockdb`，不要再跑 `docker run` |
| 連不上資料庫 | 先確認 container 有跑：`docker ps`，沒有的話執行 `docker start stockdb` |
| `.env` 密碼和 container 密碼不一致 | 兩邊設定相同密碼，`DB_PASSWORD` = `POSTGRES_PASSWORD` |
