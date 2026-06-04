"""utils/db.py — 所有資料庫讀取，Dashboard 層不直接碰 psycopg2"""

import os
import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv


def get_db_config():
    load_dotenv()
    return {
        "host":     os.getenv("DB_HOST", "localhost"),
        "port":     int(os.getenv("DB_PORT", "5433")),
        "dbname":   os.getenv("DB_NAME", "stockdb"),
        "user":     os.getenv("DB_USER", "stock_user"),
        "password": os.getenv("DB_PASSWORD"),
    }


def _clean(df):
    for col in ["latest_close","return_20d","return_60d","volatility_20d",
                "max_drawdown","volume_ratio","health_score",
                "avg_return_20d","avg_return_60d","avg_volatility","avg_health_score",
                "open","high","low","close","volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=300)
def read_latest_factors():
    q = """SELECT stock_id, name, category, date, latest_close,
                  return_20d, return_60d, volatility_20d,
                  max_drawdown, volume_ratio, health_score, cluster_label
           FROM v_latest_factors ORDER BY stock_id"""
    with psycopg2.connect(**get_db_config()) as conn:
        return _clean(pd.read_sql(q, conn))

@st.cache_data(ttl=300)
def read_industry_avg():
    q = """SELECT category, stock_count, avg_return_20d, avg_return_60d,
                  avg_volatility, avg_health_score
           FROM v_industry_avg ORDER BY avg_health_score DESC NULLS LAST"""
    with psycopg2.connect(**get_db_config()) as conn:
        return _clean(pd.read_sql(q, conn))

@st.cache_data(ttl=300)
def read_stocks():
    with psycopg2.connect(**get_db_config()) as conn:
        return pd.read_sql(
            "SELECT stock_id, name, category, market, listed_date FROM stocks ORDER BY stock_id", conn)

@st.cache_data(ttl=300)
def read_stock_prices(stock_id):
    q = "SELECT date, open, high, low, close, volume FROM daily_prices WHERE stock_id=%s ORDER BY date"
    with psycopg2.connect(**get_db_config()) as conn:
        df = pd.read_sql(q, conn, params=(stock_id,))
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = _clean(df)
    return df

@st.cache_data(ttl=300)
def read_prices_multi(stock_ids: tuple):
    ph = ",".join(["%s"]*len(stock_ids))
    q = f"SELECT stock_id, date, close FROM daily_prices WHERE stock_id IN ({ph}) ORDER BY stock_id, date"
    with psycopg2.connect(**get_db_config()) as conn:
        df = pd.read_sql(q, conn, params=stock_ids)
    df["date"]  = pd.to_datetime(df["date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df

@st.cache_data(ttl=300)
def read_quality_check():
    q = """
        SELECT s.stock_id, s.name, s.category,
               COUNT(dp.date) AS rows,
               MIN(dp.date)   AS start_date,
               MAX(dp.date)   AS end_date,
               SUM(CASE WHEN dp.close IS NULL THEN 1 ELSE 0 END)  AS missing_close,
               SUM(CASE WHEN dp.volume IS NULL THEN 1 ELSE 0 END) AS missing_volume,
               SUM(CASE WHEN dp.open<0 OR dp.high<0 OR dp.low<0 OR dp.close<0
                             OR dp.high<dp.low THEN 1 ELSE 0 END) AS abnormal_price,
               SUM(CASE WHEN dp.volume<0 THEN 1 ELSE 0 END)       AS abnormal_volume
        FROM stocks s
        LEFT JOIN daily_prices dp ON s.stock_id=dp.stock_id
        GROUP BY s.stock_id, s.name, s.category
        ORDER BY s.category, s.stock_id"""
    with psycopg2.connect(**get_db_config()) as conn:
        return pd.read_sql(q, conn)