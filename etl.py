# etl.py
# FinMind API 抓台股股價，清洗後存入 PostgreSQL
# 成員 A：Day 1-3
#
# 使用方式：
#   python etl.py                   # 抓所有股票，預設近 90 天
#   python etl.py --days 180        # 近 180 天
#   python etl.py --stock 2330      # 只抓單一股票（測試用）
#   python etl.py --init-db         # 初始化資料庫（建表 + 寫入 stock 清單）
# -------------------------------------------------------

import os
import time
import argparse
import logging
from datetime import date, timedelta

import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from stock_list import STOCK_LIST, STOCK_IDS

# ── 設定 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# 從環境變數讀取（或直接改這裡）
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "stockdb"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

FINMIND_TOKEN = os.getenv("FINMIND_TOKEN", "")   # 免費版可留空，有 token 速率較高
FINMIND_URL   = "https://api.finmindtrade.com/api/v4/data"
RATE_LIMIT_SLEEP = 1.5   # 免費版每次請求間隔秒數


# ── 資料庫連線 ─────────────────────────────────────────
def get_conn():
    return psycopg2.connect(**DB_CONFIG)


# ── 初始化資料庫 ───────────────────────────────────────
def init_db(conn):
    """執行 schema.sql 建表，並把股票清單 upsert 進 stocks 表"""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    with conn.cursor() as cur:
        cur.execute(sql)
        log.info("schema.sql 執行完成")

        # upsert 股票清單
        rows = [(s["stock_id"], s["name"], s["category"], s["market"])
                for s in STOCK_LIST]
        execute_values(
            cur,
            """
            INSERT INTO stocks (stock_id, name, category, market)
            VALUES %s
            ON CONFLICT (stock_id) DO UPDATE
                SET name     = EXCLUDED.name,
                    category = EXCLUDED.category,
                    market   = EXCLUDED.market
            """,
            rows,
        )
        log.info(f"stocks 表已寫入 {len(rows)} 筆")
    conn.commit()


# ── FinMind API ────────────────────────────────────────
def fetch_price(stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """向 FinMind 抓單支股票的日 K 資料，回傳 DataFrame"""
    params = {
        "dataset":    "TaiwanStockPrice",
        "data_id":    stock_id,
        "start_date": start_date,
        "end_date":   end_date,
    }
    if FINMIND_TOKEN:
        params["token"] = FINMIND_TOKEN

    try:
        resp = requests.get(FINMIND_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != 200:
            log.warning(f"{stock_id} API 回應非 200：{data.get('msg')}")
            return pd.DataFrame()
        return pd.DataFrame(data["data"])
    except Exception as e:
        log.error(f"{stock_id} 請求失敗：{e}")
        return pd.DataFrame()


# ── 清洗 ───────────────────────────────────────────────
def clean_prices(df: pd.DataFrame, stock_id: str) -> pd.DataFrame:
    """清洗股價資料：重命名欄位、型別轉換、去空值與重複"""
    if df.empty:
        return df

    # FinMind 欄位名稱對應
    col_map = {
        "date":              "date",
        "open":              "open",
        "max":               "high",
        "min":               "low",
        "close":             "close",
        "Trading_Volume":    "volume",
        "Trading_money":     "trade_value",
    }
    df = df.rename(columns=col_map)

    # 只保留需要的欄位（有些欄位 FinMind 可能沒有）
    keep = ["date", "open", "high", "low", "close", "volume", "trade_value"]
    df = df[[c for c in keep if c in df.columns]].copy()

    # 型別
    df["date"]  = pd.to_datetime(df["date"]).dt.date
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["volume", "trade_value"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # 去除 close 為空（必要欄位）
    before = len(df)
    df = df.dropna(subset=["close"])
    df = df.drop_duplicates(subset=["date"])
    after = len(df)
    if before != after:
        log.debug(f"{stock_id} 清洗後從 {before} 筆減為 {after} 筆")

    df["stock_id"] = stock_id
    return df


# ── 入庫 ───────────────────────────────────────────────
def upsert_prices(conn, df: pd.DataFrame):
    """將清洗後的 DataFrame upsert 進 daily_prices"""
    if df.empty:
        return 0

    cols = ["stock_id", "date", "open", "high", "low", "close", "volume", "trade_value"]
    rows = []
    for _, row in df.iterrows():
        rows.append(tuple(
            None if pd.isna(row.get(c)) else row.get(c)
            for c in cols
        ))

    with conn.cursor() as cur:
        execute_values(
            cur,
            f"""
            INSERT INTO daily_prices ({', '.join(cols)})
            VALUES %s
            ON CONFLICT (stock_id, date) DO UPDATE
                SET open        = EXCLUDED.open,
                    high        = EXCLUDED.high,
                    low         = EXCLUDED.low,
                    close       = EXCLUDED.close,
                    volume      = EXCLUDED.volume,
                    trade_value = EXCLUDED.trade_value
            """,
            rows,
        )
    conn.commit()
    return len(rows)


# ── 主流程 ─────────────────────────────────────────────
def run_etl(stock_ids: list, days: int):
    end_date   = date.today().isoformat()
    start_date = (date.today() - timedelta(days=days)).isoformat()
    log.info(f"ETL 開始：{start_date} → {end_date}，共 {len(stock_ids)} 支")

    conn = get_conn()
    total = 0

    for i, sid in enumerate(stock_ids, 1):
        log.info(f"[{i}/{len(stock_ids)}] 抓取 {sid} ...")
        raw_df    = fetch_price(sid, start_date, end_date)
        clean_df  = clean_prices(raw_df, sid)
        n         = upsert_prices(conn, clean_df)
        total    += n
        log.info(f"  {sid} 入庫 {n} 筆")

        if i < len(stock_ids):
            time.sleep(RATE_LIMIT_SLEEP)   # 避免觸發速率限制

    conn.close()
    log.info(f"ETL 完成，共入庫 {total} 筆")


# ── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinMind 股價 ETL")
    parser.add_argument("--days",     type=int, default=90,   help="抓近幾天（預設 90）")
    parser.add_argument("--stock",    type=str, default=None, help="只抓單一股票代號")
    parser.add_argument("--init-db",  action="store_true",    help="初始化資料庫（建表 + 寫入股票清單）")
    args = parser.parse_args()

    if args.init_db:
        log.info("初始化資料庫 ...")
        conn = get_conn()
        init_db(conn)
        conn.close()
        log.info("初始化完成")

    ids = [args.stock] if args.stock else STOCK_IDS
    run_etl(ids, args.days)
