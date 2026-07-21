"""routers/data_health.py - 資料健康檢查 API"""

from fastapi import APIRouter
from db import query, query_one

router = APIRouter(prefix="/api/data-health", tags=["data-health"])


@router.get("")
def data_health():
    summary = query_one("""
        WITH
            stock_total AS (
                SELECT COUNT(*) AS stock_count FROM stocks
            ),
            price_stats AS (
                SELECT
                    COUNT(*) AS price_rows,
                    COUNT(DISTINCT stock_id) AS price_stock_count,
                    MIN(date) AS earliest_price_date,
                    MAX(date) AS latest_price_date
                FROM daily_prices
            ),
            factor_stats AS (
                SELECT
                    COUNT(*) AS factor_rows,
                    COUNT(DISTINCT stock_id) AS factor_stock_count,
                    MIN(date) AS earliest_factor_date,
                    MAX(date) AS latest_factor_date
                FROM factor_scores
            ),
            latest_price AS (
                SELECT stock_id, MAX(date) AS latest_date, COUNT(*) AS row_count
                FROM daily_prices
                GROUP BY stock_id
            ),
            latest_factor AS (
                SELECT stock_id, MAX(date) AS latest_date, COUNT(*) AS row_count
                FROM factor_scores
                GROUP BY stock_id
            ),
            per_stock AS (
                SELECT
                    s.stock_id,
                    COALESCE(lp.row_count, 0) AS price_days,
                    COALESCE(lf.row_count, 0) AS factor_days
                FROM stocks s
                LEFT JOIN latest_price lp USING (stock_id)
                LEFT JOIN latest_factor lf USING (stock_id)
            )
        SELECT
            st.stock_count,
            ps.price_rows,
            fs.factor_rows,
            ps.earliest_price_date,
            ps.latest_price_date,
            fs.earliest_factor_date,
            fs.latest_factor_date,
            COALESCE(ROUND(
                (COALESCE(ps.price_stock_count, 0)::NUMERIC / NULLIF(st.stock_count, 0)) * 100,
                1
            ), 0) AS price_coverage_pct,
            COALESCE(ROUND(
                (COALESCE(fs.factor_stock_count, 0)::NUMERIC / NULLIF(st.stock_count, 0)) * 100,
                1
            ), 0) AS factor_coverage_pct,
            (
                SELECT COUNT(*)
                FROM stocks s
                LEFT JOIN latest_price lp USING (stock_id)
                WHERE lp.latest_date IS NULL OR lp.latest_date < ps.latest_price_date
            ) AS stale_price_count,
            (
                SELECT COUNT(*)
                FROM stocks s
                LEFT JOIN latest_factor lf USING (stock_id)
                WHERE lf.latest_date IS NULL OR lf.latest_date < fs.latest_factor_date
            ) AS stale_factor_count,
            COALESCE((SELECT ROUND(AVG(price_days)::NUMERIC, 1) FROM per_stock), 0) AS avg_price_days,
            COALESCE((SELECT ROUND(AVG(factor_days)::NUMERIC, 1) FROM per_stock), 0) AS avg_factor_days
        FROM stock_total st
        CROSS JOIN price_stats ps
        CROSS JOIN factor_stats fs
        GROUP BY
            st.stock_count,
            ps.price_rows,
            fs.factor_rows,
            ps.earliest_price_date,
            ps.latest_price_date,
            fs.earliest_factor_date,
            fs.latest_factor_date,
            ps.price_stock_count,
            fs.factor_stock_count
    """) or {}

    by_category = query("""
        WITH
            latest_price AS (
                SELECT stock_id, MAX(date) AS latest_price_date, COUNT(*) AS price_days
                FROM daily_prices
                GROUP BY stock_id
            ),
            latest_factor AS (
                SELECT stock_id, MAX(date) AS latest_factor_date, COUNT(*) AS factor_days
                FROM factor_scores
                GROUP BY stock_id
            )
        SELECT
            s.category,
            COUNT(*) AS stock_count,
            COUNT(lp.stock_id) AS price_stock_count,
            COUNT(lf.stock_id) AS factor_stock_count,
            ROUND(AVG(COALESCE(lp.price_days, 0))::NUMERIC, 1) AS avg_price_days,
            ROUND(AVG(COALESCE(lf.factor_days, 0))::NUMERIC, 1) AS avg_factor_days
        FROM stocks s
        LEFT JOIN latest_price lp USING (stock_id)
        LEFT JOIN latest_factor lf USING (stock_id)
        GROUP BY s.category
        ORDER BY s.category
    """)

    stale_stocks = query("""
        WITH
            max_dates AS (
                SELECT
                    (SELECT MAX(date) FROM daily_prices) AS global_price_date,
                    (SELECT MAX(date) FROM factor_scores) AS global_factor_date
            ),
            latest_price AS (
                SELECT stock_id, MAX(date) AS latest_price_date, COUNT(*) AS price_days
                FROM daily_prices
                GROUP BY stock_id
            ),
            latest_factor AS (
                SELECT stock_id, MAX(date) AS latest_factor_date, COUNT(*) AS factor_days
                FROM factor_scores
                GROUP BY stock_id
            )
        SELECT
            s.stock_id,
            s.name,
            s.category,
            lp.latest_price_date,
            lf.latest_factor_date,
            COALESCE(lp.price_days, 0) AS price_days,
            COALESCE(lf.factor_days, 0) AS factor_days,
            CASE
                WHEN lp.latest_price_date IS NULL THEN 'missing_price'
                WHEN lf.latest_factor_date IS NULL THEN 'missing_factor'
                WHEN lp.latest_price_date < md.global_price_date THEN 'stale_price'
                WHEN lf.latest_factor_date < md.global_factor_date THEN 'stale_factor'
                ELSE 'ok'
            END AS status
        FROM stocks s
        CROSS JOIN max_dates md
        LEFT JOIN latest_price lp USING (stock_id)
        LEFT JOIN latest_factor lf USING (stock_id)
        WHERE
            lp.latest_price_date IS NULL
            OR lf.latest_factor_date IS NULL
            OR lp.latest_price_date < md.global_price_date
            OR lf.latest_factor_date < md.global_factor_date
        ORDER BY
            CASE
                WHEN lp.latest_price_date IS NULL THEN 1
                WHEN lf.latest_factor_date IS NULL THEN 2
                WHEN lp.latest_price_date < md.global_price_date THEN 3
                WHEN lf.latest_factor_date < md.global_factor_date THEN 4
                ELSE 5
            END,
            s.stock_id
        LIMIT 50
    """)

    factor_quality = query_one("""
        SELECT
            COUNT(*) FILTER (WHERE return_20d IS NULL) AS missing_return_20d,
            COUNT(*) FILTER (WHERE return_60d IS NULL) AS missing_return_60d,
            COUNT(*) FILTER (WHERE volatility_20d IS NULL) AS missing_volatility_20d,
            COUNT(*) FILTER (WHERE max_drawdown IS NULL) AS missing_max_drawdown,
            COUNT(*) FILTER (WHERE volume_ratio IS NULL) AS missing_volume_ratio,
            COUNT(*) FILTER (WHERE health_score IS NULL) AS missing_health_score,
            COUNT(*) FILTER (WHERE cluster_label IS NULL) AS missing_cluster_label
        FROM factor_scores
        WHERE date = (SELECT MAX(date) FROM factor_scores)
    """) or {}

    return {
        "summary": summary,
        "by_category": by_category,
        "stale_stocks": stale_stocks,
        "factor_quality": factor_quality,
    }
