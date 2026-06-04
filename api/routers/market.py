"""routers/market.py — 市場總覽相關 API"""

from fastapi import APIRouter
from db import query, query_one

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/overview")
def market_overview():
    """KPI：追蹤股票數、最新日期、平均健康分數、20日報酬最佳"""
    row = query_one("""
        SELECT
            COUNT(*)                                    AS stock_count,
            MAX(date)                                   AS latest_date,
            ROUND(AVG(health_score)::NUMERIC, 1)        AS avg_health_score,
            (SELECT stock_id FROM v_latest_factors
             ORDER BY return_20d DESC NULLS LAST LIMIT 1) AS best_return_id,
            (SELECT name FROM v_latest_factors
             ORDER BY return_20d DESC NULLS LAST LIMIT 1) AS best_return_name,
            (SELECT ROUND((return_20d * 100)::NUMERIC, 2)
             FROM v_latest_factors
             ORDER BY return_20d DESC NULLS LAST LIMIT 1) AS best_return_pct
        FROM v_latest_factors
    """)
    return row


@router.get("/health-scatter")
def health_scatter():
    """市場健康分布散點圖資料"""
    return query("""
        SELECT stock_id, name, category,
               ROUND((return_20d * 100)::NUMERIC, 2)    AS return_20d_pct,
               ROUND((volatility_20d * 100)::NUMERIC, 2) AS volatility_pct,
               ROUND(health_score::NUMERIC, 1)           AS health_score
        FROM v_latest_factors
        WHERE return_20d IS NOT NULL AND volatility_20d IS NOT NULL
        ORDER BY health_score DESC
    """)


@router.get("/industry-avg")
def industry_avg():
    """產業平均健康分數"""
    return query("""
        SELECT category, stock_count,
               ROUND((avg_return_20d * 100)::NUMERIC, 2) AS avg_return_20d_pct,
               ROUND((avg_return_60d * 100)::NUMERIC, 2) AS avg_return_60d_pct,
               ROUND(avg_health_score::NUMERIC, 1)        AS avg_health_score
        FROM v_industry_avg
        ORDER BY avg_health_score DESC
    """)