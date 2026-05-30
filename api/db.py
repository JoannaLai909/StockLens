"""api/db.py — PostgreSQL 連線與通用查詢工具"""

import os
from contextlib import contextmanager
from typing import Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def get_db_config() -> dict:
    return {
        "host":     os.getenv("DB_HOST", "localhost"),
        "port":     int(os.getenv("DB_PORT", "5432")),
        "dbname":   os.getenv("DB_NAME", "stockdb"),
        "user":     os.getenv("DB_USER", "stock_user"),
        "password": os.getenv("DB_PASSWORD"),
    }


@contextmanager
def get_conn():
    conn = psycopg2.connect(**get_db_config())
    try:
        yield conn
    finally:
        conn.close()


def query(sql: str, params=None) -> list[dict[str, Any]]:
    """執行 SELECT，回傳 list[dict]"""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return [dict(row) for row in cur.fetchall()]


def query_one(sql: str, params=None) -> dict[str, Any] | None:
    rows = query(sql, params)
    return rows[0] if rows else None