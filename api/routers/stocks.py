"""routers/stocks.py — 個股資料"""

from fastapi import APIRouter, HTTPException, Query
from db import query, query_one

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


def _cluster_summary(profile: dict | None) -> dict:
    """把 K-means 的數字群組轉成 Dashboard 可理解的文字說明。"""
    if not profile:
        return {
            "cluster_name": None,
            "cluster_description": "目前尚未完成分群，請先執行因子計算與 K-means。",
        }

    health = float(profile["avg_health_score"] or 0)
    ret60 = float(profile["avg_return_60d_pct"] or 0)
    vol = float(profile["avg_volatility_pct"] or 0)
    drawdown = float(profile["avg_max_drawdown_pct"] or 0)

    if health >= 70 and vol <= 18 and drawdown >= -12:
        name = "穩健成長型"
        desc = "同群平均健康分數較高，波動與回撤相對可控，適合優先觀察中長期表現。"
    elif ret60 >= 10 and vol > 18:
        name = "高動能波動型"
        desc = "同群近期報酬表現較強，但波動也偏高，適合搭配風險控管一起判斷。"
    elif health < 55 or drawdown < -15:
        name = "風險偏高型"
        desc = "同群健康分數較低或最大回撤較深，代表近期風險較明顯，需要保守看待。"
    elif vol <= 14:
        name = "防禦穩定型"
        desc = "同群波動相對低，價格變動較穩定，但仍需搭配報酬率確認成長性。"
    else:
        name = "中性觀察型"
        desc = "同群表現介於成長與風險之間，建議搭配產業、報酬率與成交量變化一起比較。"

    return {
        "cluster_name": name,
        "cluster_description": desc,
    }


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

    profile = None
    if row.get("cluster_label") is not None:
        profile = query_one("""
            SELECT cluster_label,
                   COUNT(*) AS cluster_stock_count,
                   ROUND(AVG(health_score)::NUMERIC, 1) AS avg_health_score,
                   ROUND((AVG(return_20d) * 100)::NUMERIC, 2) AS avg_return_20d_pct,
                   ROUND((AVG(return_60d) * 100)::NUMERIC, 2) AS avg_return_60d_pct,
                   ROUND((AVG(volatility_20d) * 100)::NUMERIC, 2) AS avg_volatility_pct,
                   ROUND((AVG(max_drawdown) * 100)::NUMERIC, 2) AS avg_max_drawdown_pct
            FROM factor_scores
            WHERE date = %s
              AND cluster_label = %s
            GROUP BY cluster_label
        """, (row["date"], row["cluster_label"]))

    row.update(_cluster_summary(profile))
    if profile:
        row.update({
            "cluster_stock_count": profile["cluster_stock_count"],
            "cluster_avg_health_score": profile["avg_health_score"],
            "cluster_avg_return_60d_pct": profile["avg_return_60d_pct"],
            "cluster_avg_volatility_pct": profile["avg_volatility_pct"],
        })
    else:
        row.update({
            "cluster_stock_count": None,
            "cluster_avg_health_score": None,
            "cluster_avg_return_60d_pct": None,
            "cluster_avg_volatility_pct": None,
        })

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
