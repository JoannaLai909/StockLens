"""routers/rankings.py — 因子排行"""

from fastapi import APIRouter, Query
from db import query

router = APIRouter(prefix="/api/rankings", tags=["rankings"])

VALID_METRICS = {
    "return_20d", "return_60d", "health_score",
    "volatility_20d", "max_drawdown", "volume_ratio",
}

VALID_CATEGORIES = {
    "semiconductor", "financial", "etf",
    "electronics", "shipping", "telecom", "other",
}


@router.get("")
def get_rankings(
    metric:   str = Query("return_20d", description="排序指標"),
    order:    str = Query("desc",       description="asc | desc"),
    category: str = Query("all",        description="產業篩選"),
    limit:    int = Query(30,           ge=1, le=100),
):
    if metric not in VALID_METRICS:
        metric = "return_20d"

    order_sql = "DESC NULLS LAST" if order != "asc" else "ASC NULLS LAST"

    cat_filter = ""
    params: list = []
    if category != "all" and category in VALID_CATEGORIES:
        cat_filter = "AND category = %s"
        params.append(category)

    params.append(limit)

    rows = query(f"""
        SELECT stock_id, name, category,
               ROUND((return_20d    * 100)::NUMERIC, 2) AS return_20d_pct,
               ROUND((return_60d    * 100)::NUMERIC, 2) AS return_60d_pct,
               ROUND((volatility_20d* 100)::NUMERIC, 2) AS volatility_pct,
               ROUND((max_drawdown  * 100)::NUMERIC, 2) AS max_drawdown_pct,
               ROUND(volume_ratio::NUMERIC, 2)           AS volume_ratio,
               ROUND(health_score::NUMERIC, 1)           AS health_score,
               cluster_label,
               ROUND(latest_close::NUMERIC, 2)           AS latest_close
        FROM v_latest_factors
        WHERE {metric} IS NOT NULL {cat_filter}
        ORDER BY {metric} {order_sql}
        LIMIT %s
    """, params)
    return rows