"""routers/stocks.py — 個股資料"""

from fastapi import APIRouter, HTTPException, Query
from db import query, query_one

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("")
def list_stocks():
    return query("SELECT stock_id, name, category, market FROM stocks ORDER BY stock_id")


@router.get("/{stock_id}")
def get_stock(stock_id: str):
    row = query_one("""
        SELECT s.stock_id, s.name, s.category, s.market,
               f.date, f.latest_close,
               ROUND((f.return_20d    * 100)::NUMERIC, 2) AS return_20d_pct,
               ROUND((f.return_60d    * 100)::NUMERIC, 2) AS return_60d_pct,
               ROUND((f.volatility_20d* 100)::NUMERIC, 2) AS volatility_pct,
               ROUND((f.max_drawdown  * 100)::NUMERIC, 2) AS max_drawdown_pct,
               ROUND(f.volume_ratio::NUMERIC, 2)           AS volume_ratio,
               ROUND(f.health_score::NUMERIC, 1)           AS health_score,
               f.cluster_label
        FROM stocks s
        JOIN v_latest_factors f USING (stock_id)
        WHERE s.stock_id = %s
    """, (stock_id,))
    if not row:
        raise HTTPException(status_code=404, detail=f"股票 {stock_id} 不存在")
    return row


@router.get("/{stock_id}/prices")
def get_prices(
    stock_id: str,
    days: int = Query(126, ge=1, le=500, description="取近幾天"),
):
    rows = query("""
        SELECT date, open, high, low,
               ROUND(close::NUMERIC, 2)  AS close,
               volume
        FROM daily_prices
        WHERE stock_id = %s
          AND date >= CURRENT_DATE - INTERVAL '1 day' * %s
        ORDER BY date ASC
    """, (stock_id, days))
    if not rows:
        raise HTTPException(status_code=404, detail=f"股票 {stock_id} 無價格資料")
    return rows


@router.get("/{stock_id}/factors-history")
def get_factors_history(
    stock_id: str,
    days: int = Query(90, ge=1, le=500),
):
    return query("""
        SELECT date,
               ROUND((return_20d    * 100)::NUMERIC, 2) AS return_20d_pct,
               ROUND((return_60d    * 100)::NUMERIC, 2) AS return_60d_pct,
               ROUND((volatility_20d* 100)::NUMERIC, 2) AS volatility_pct,
               ROUND(health_score::NUMERIC, 1)           AS health_score
        FROM factor_scores
        WHERE stock_id = %s
          AND date >= CURRENT_DATE - INTERVAL '1 day' * %s
        ORDER BY date ASC
    """, (stock_id, days))