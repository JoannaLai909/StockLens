import os
import argparse
import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


def get_connection():
    load_dotenv()

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "stockdb"),
        user=os.getenv("DB_USER", "stock_user"),
        password=os.getenv("DB_PASSWORD"),
    )


def read_daily_prices(conn, stock_id=None):
    if stock_id:
        query = """
            SELECT stock_id, date, close, volume
            FROM daily_prices
            WHERE stock_id = %s
            ORDER BY stock_id, date;
        """
        df = pd.read_sql(query, conn, params=(stock_id,))
    else:
        query = """
            SELECT stock_id, date, close, volume
            FROM daily_prices
            ORDER BY stock_id, date;
        """
        df = pd.read_sql(query, conn)

    df["date"] = pd.to_datetime(df["date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    return df


def calc_max_drawdown(series):
    running_max = series.cummax()
    drawdown = series / running_max - 1
    return drawdown.min()


def min_max_score(series, higher_is_better=True):
    series = series.astype(float)

    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series(50, index=series.index)

    score = (series - min_val) / (max_val - min_val) * 100

    if not higher_is_better:
        score = 100 - score

    return score.clip(0, 100)


def calculate_factors(df):
    if df.empty:
        return pd.DataFrame()

    result_list = []

    for stock_id, group in df.groupby("stock_id"):
        g = group.copy()
        g = g.sort_values("date")

        g["daily_return"] = g["close"].pct_change()

        g["return_20d"] = g["close"] / g["close"].shift(20) - 1
        g["return_60d"] = g["close"] / g["close"].shift(60) - 1

        g["volatility_20d"] = g["daily_return"].rolling(window=20).std()

        g["max_drawdown"] = (
            g["close"]
            .rolling(window=60)
            .apply(calc_max_drawdown, raw=False)
        )

        volume_ma_5 = g["volume"].rolling(window=5).mean()
        volume_ma_20 = g["volume"].rolling(window=20).mean()
        g["volume_ratio"] = volume_ma_5 / volume_ma_20

        result_list.append(g)

    factors = pd.concat(result_list, ignore_index=True)

    factor_cols = [
        "return_20d",
        "return_60d",
        "volatility_20d",
        "max_drawdown",
        "volume_ratio",
    ]

    factors[factor_cols] = factors[factor_cols].replace([np.inf, -np.inf], np.nan)

    # 先只保留可以計算完整 60 日因子的資料
    factors = factors.dropna(
        subset=[
            "return_20d",
            "return_60d",
            "volatility_20d",
            "max_drawdown",
            "volume_ratio",
        ]
    ).copy()

    if factors.empty:
        return factors

    # 建立 health_score
    factors["return_20d_score"] = min_max_score(factors["return_20d"], True)
    factors["return_60d_score"] = min_max_score(factors["return_60d"], True)
    factors["volatility_score"] = min_max_score(factors["volatility_20d"], False)

    # max_drawdown 通常是負數，越接近 0 越好，所以 higher_is_better=True
    factors["drawdown_score"] = min_max_score(factors["max_drawdown"], True)

    # volume_ratio 不是越高越好到無限，這裡先用簡化版：越高代表關注度越高
    factors["volume_score"] = min_max_score(factors["volume_ratio"], True)

    factors["health_score"] = (
        0.30 * factors["return_20d_score"]
        + 0.25 * factors["return_60d_score"]
        + 0.20 * factors["volatility_score"]
        + 0.15 * factors["drawdown_score"]
        + 0.10 * factors["volume_score"]
    )

    output_cols = [
        "stock_id",
        "date",
        "return_20d",
        "return_60d",
        "volatility_20d",
        "max_drawdown",
        "volume_ratio",
        "health_score",
    ]

    return factors[output_cols]


def upsert_factor_scores(conn, factors):
    if factors.empty:
        print("沒有可寫入的 factor_scores，可能資料天數不足。")
        return 0

    sql = """
        INSERT INTO factor_scores (
            stock_id,
            date,
            return_20d,
            return_60d,
            volatility_20d,
            max_drawdown,
            volume_ratio,
            health_score,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (stock_id, date)
        DO UPDATE SET
            return_20d = EXCLUDED.return_20d,
            return_60d = EXCLUDED.return_60d,
            volatility_20d = EXCLUDED.volatility_20d,
            max_drawdown = EXCLUDED.max_drawdown,
            volume_ratio = EXCLUDED.volume_ratio,
            health_score = EXCLUDED.health_score,
            updated_at = NOW();
    """

    rows = []
    for _, row in factors.iterrows():
        rows.append(
            (
                row["stock_id"],
                row["date"].date(),
                round(float(row["return_20d"]), 4),
                round(float(row["return_60d"]), 4),
                round(float(row["volatility_20d"]), 4),
                round(float(row["max_drawdown"]), 4),
                round(float(row["volume_ratio"]), 4),
                round(float(row["health_score"]), 2),
            )
        )

    with conn.cursor() as cur:
        cur.executemany(sql, rows)

    conn.commit()
    return len(rows)

def update_cluster_labels(conn, n_clusters=3):
    """
    使用最新日期的 factor_scores 做 K-means 分群，
    並將結果寫回同一天資料的 cluster_label 欄位。
    """
    query = """
        SELECT stock_id, date, return_20d, return_60d,
               volatility_20d, max_drawdown, volume_ratio, health_score
        FROM factor_scores
        WHERE date = (SELECT MAX(date) FROM factor_scores)
          AND return_20d IS NOT NULL
          AND return_60d IS NOT NULL
          AND volatility_20d IS NOT NULL
          AND max_drawdown IS NOT NULL
          AND volume_ratio IS NOT NULL
          AND health_score IS NOT NULL
        ORDER BY stock_id;
    """

    df = pd.read_sql(query, conn)

    if df.empty:
        print("沒有可分群的資料，請先計算 factor_scores。")
        return 0

    feature_cols = [
        "return_20d",
        "return_60d",
        "volatility_20d",
        "max_drawdown",
        "volume_ratio",
        "health_score",
    ]

    if len(df) < n_clusters:
        n_clusters = len(df)

    x = df[feature_cols].astype(float)

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster_label"] = model.fit_predict(x_scaled)

    sql = """
        UPDATE factor_scores
        SET cluster_label = %s,
            updated_at = NOW()
        WHERE stock_id = %s
          AND date = %s;
    """

    rows = []
    for _, row in df.iterrows():
        rows.append(
            (
                int(row["cluster_label"]),
                row["stock_id"],
                row["date"],
            )
        )

    with conn.cursor() as cur:
        cur.executemany(sql, rows)

    conn.commit()

    print(f"K-means 分群完成：最新日期 {df['date'].iloc[0]}，共 {len(rows)} 支股票")
    return len(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", help="只計算單一股票，例如 2330")
    parser.add_argument("--cluster", action="store_true", help="執行 K-means 分群")
    args = parser.parse_args()

    print("開始計算量化因子...")

    conn = get_connection()

    try:
        prices = read_daily_prices(conn, stock_id=args.stock)
        print(f"已讀取 daily_prices：{len(prices)} 筆")

        factors = calculate_factors(prices)
        print(f"已計算 factor_scores：{len(factors)} 筆")

        inserted = upsert_factor_scores(conn, factors)
        print(f"factor_scores 寫入完成：{inserted} 筆")

        if args.cluster:
            update_cluster_labels(conn)

    finally:
        conn.close()

    print("量化因子計算完成。")


if __name__ == "__main__":
    main()