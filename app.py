import os

import altair as alt
import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv


st.set_page_config(
    page_title="StockLens | 台股量化因子分析平台",
    page_icon="📈",
    layout="wide",
)


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }
    .hero {
        padding: 2.4rem 2.6rem;
        border-radius: 8px;
        background: linear-gradient(135deg, #0f172a 0%, #1f2937 54%, #134e4a 100%);
        color: white;
        margin-bottom: 1.5rem;
    }
    .hero h1 {
        font-size: 2.35rem;
        line-height: 1.25;
        margin-bottom: 0.75rem;
        color: #ffffff;
    }
    .hero p {
        color: #d1d5db;
        font-size: 1.05rem;
        margin-bottom: 0;
    }
    .section-title {
        margin-top: 1.4rem;
        margin-bottom: 0.65rem;
        font-size: 1.35rem;
        font-weight: 700;
        color: #111827;
    }
    .info-panel {
        padding: 1.1rem 1.2rem;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background: #ffffff;
        min-height: 128px;
    }
    .info-panel h3 {
        font-size: 1rem;
        margin-bottom: 0.55rem;
        color: #111827;
    }
    .info-panel p, .info-panel li {
        color: #4b5563;
        font-size: 0.95rem;
    }
    .metric-strip {
        border-left: 4px solid #0f766e;
        padding: 0.8rem 1rem;
        background: #f8fafc;
        border-radius: 6px;
        color: #334155;
        margin: 0.7rem 0 1rem;
    }
    .page-divider {
        margin: 2.2rem 0 1.5rem;
        border-top: 1px solid #e5e7eb;
    }
    .page-subtitle {
        color: #4b5563;
        margin-bottom: 1rem;
    }
    .note {
        border-left: 4px solid #0f766e;
        padding: 0.7rem 0.9rem;
        background: #f8fafc;
        border-radius: 6px;
        color: #334155;
        margin-bottom: 1rem;
    }
    .summary-box {
        padding: 1rem 1.1rem;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background: #ffffff;
        color: #334155;
        line-height: 1.75;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_db_config():
    load_dotenv()

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5433")),
        "dbname": os.getenv("DB_NAME", "stockdb"),
        "user": os.getenv("DB_USER", "stock_user"),
        "password": os.getenv("DB_PASSWORD"),
    }


@st.cache_data(ttl=300)
def load_latest_factors():
    query = """
        SELECT
            stock_id,
            name,
            category,
            date,
            latest_close,
            return_20d,
            return_60d,
            volatility_20d,
            max_drawdown,
            volume_ratio,
            health_score
        FROM v_latest_factors;
    """

    with psycopg2.connect(**get_db_config()) as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def load_stocks():
    query = """
        SELECT stock_id, name, category
        FROM stocks
        ORDER BY stock_id;
    """

    with psycopg2.connect(**get_db_config()) as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def load_stock_detail(stock_id):
    price_query = """
        SELECT date, close, volume
        FROM daily_prices
        WHERE stock_id = %s
        ORDER BY date;
    """
    factor_query = """
        SELECT
            stock_id,
            name,
            category,
            date,
            latest_close,
            return_20d,
            return_60d,
            volatility_20d,
            max_drawdown,
            volume_ratio,
            health_score
        FROM v_latest_factors
        WHERE stock_id = %s;
    """

    with psycopg2.connect(**get_db_config()) as conn:
        prices = pd.read_sql(price_query, conn, params=(stock_id,))
        latest_factor = pd.read_sql(factor_query, conn, params=(stock_id,))

    if not prices.empty:
        prices["date"] = pd.to_datetime(prices["date"])
        prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
        prices["volume"] = pd.to_numeric(prices["volume"], errors="coerce")

    return prices, latest_factor


def format_table(df, metric_col):
    table = df.copy()
    table.insert(0, "rank", range(1, len(table) + 1))

    percent_cols = ["return_20d", "return_60d", "volatility_20d", "max_drawdown"]
    for col in percent_cols:
        if col in table.columns:
            table[col] = table[col].apply(
                lambda value: f"{value * 100:.2f}%" if pd.notna(value) else "-"
            )

    if "volume_ratio" in table.columns:
        table["volume_ratio"] = table["volume_ratio"].apply(
            lambda value: f"{value:.2f}x" if pd.notna(value) else "-"
        )

    if "latest_close" in table.columns:
        table["latest_close"] = table["latest_close"].apply(
            lambda value: f"{value:.2f}" if pd.notna(value) else "-"
        )

    if "health_score" in table.columns:
        table["health_score"] = table["health_score"].apply(
            lambda value: f"{value:.2f}" if pd.notna(value) else "-"
        )

    return table[
        [
            "rank",
            "stock_id",
            "name",
            "category",
            "latest_close",
            metric_col,
            "health_score",
        ]
    ]


def render_top10(title, df, metric_col, label, ascending=False, use_abs_chart=False):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

    ranked = (
        df.dropna(subset=[metric_col])
        .sort_values(metric_col, ascending=ascending)
        .head(10)
        .copy()
    )

    if ranked.empty:
        st.info("目前沒有足夠資料可以產生這個排行榜。")
        return

    chart_df = ranked.copy()
    chart_df["stock_label"] = chart_df["stock_id"] + " " + chart_df["name"]
    chart_df["chart_value"] = chart_df[metric_col].abs() if use_abs_chart else chart_df[metric_col]

    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("chart_value:Q", title=label),
            y=alt.Y("stock_label:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("stock_id:N", title="股票代號"),
                alt.Tooltip("name:N", title="名稱"),
                alt.Tooltip(metric_col + ":Q", title=label, format=".4f"),
                alt.Tooltip("health_score:Q", title="Health Score", format=".2f"),
            ],
            color=alt.value("#0f766e"),
        )
        .properties(height=300)
    )

    table_col, chart_col = st.columns([1.05, 1])
    with table_col:
        st.dataframe(
            format_table(ranked, metric_col),
            use_container_width=True,
            hide_index=True,
        )
    with chart_col:
        st.altair_chart(chart, use_container_width=True)


def format_percent(value):
    return f"{value * 100:.2f}%" if pd.notna(value) else "-"


def format_ratio(value):
    return f"{value:.2f}x" if pd.notna(value) else "-"


def format_score(value):
    return f"{value:.2f}" if pd.notna(value) else "-"


def make_system_summary(stock_name, factor_row):
    health = factor_row["health_score"]
    return_20d = factor_row["return_20d"]
    return_60d = factor_row["return_60d"]
    volatility = factor_row["volatility_20d"]
    max_drawdown = factor_row["max_drawdown"]
    volume_ratio = factor_row["volume_ratio"]

    if pd.isna(health):
        health_comment = "目前健康分數不足，建議先補齊資料後再判讀。"
    elif health >= 70:
        health_comment = "整體健康分數偏高，近期量化表現相對穩健。"
    elif health >= 50:
        health_comment = "整體健康分數位於中段，表現普通，仍需要搭配風險指標觀察。"
    else:
        health_comment = "整體健康分數偏低，近期風險或表現可能較不理想。"

    trend_comment = "短中期報酬率訊號尚不明確。"
    if pd.notna(return_20d) and pd.notna(return_60d):
        if return_20d > 0 and return_60d > 0:
            trend_comment = "20 日與 60 日報酬率皆為正，短中期走勢偏強。"
        elif return_20d < 0 and return_60d < 0:
            trend_comment = "20 日與 60 日報酬率皆為負，短中期走勢偏弱。"
        elif return_20d > return_60d:
            trend_comment = "20 日報酬率優於 60 日報酬率，近期動能有轉強跡象。"

    risk_comment = "風險指標資料不足。"
    if pd.notna(volatility) and pd.notna(max_drawdown):
        risk_comment = (
            f"目前 20 日波動率為 {format_percent(volatility)}，"
            f"最大回撤為 {format_percent(max_drawdown)}，可用來衡量近期震盪與下跌風險。"
        )

    volume_comment = "成交量倍率資料不足。"
    if pd.notna(volume_ratio):
        if volume_ratio >= 1.2:
            volume_comment = f"成交量倍率為 {format_ratio(volume_ratio)}，近期量能高於 20 日均量。"
        elif volume_ratio <= 0.8:
            volume_comment = f"成交量倍率為 {format_ratio(volume_ratio)}，近期量能低於 20 日均量。"
        else:
            volume_comment = f"成交量倍率為 {format_ratio(volume_ratio)}，近期量能大致接近均量。"

    return f"{stock_name}：{health_comment} {trend_comment} {risk_comment} {volume_comment}"


st.markdown(
    """
    <div class="hero">
        <h1>基於 Linux 與 Docker 的台股量化因子分析平台</h1>
        <p>
            StockLens 整合台股資料擷取、資料庫儲存、量化因子計算與視覺化儀表板，
            協助使用者用一致且可重現的流程觀察股票表現。
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown('<div class="section-title">專題目的</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="metric-strip">
        建立一套從資料收集、清洗、儲存、因子計算到視覺化呈現的台股分析流程，
        讓使用者能快速比較個股近期報酬、波動、回撤與綜合健康分數。
    </div>
    """,
    unsafe_allow_html=True,
)

purpose_col1, purpose_col2, purpose_col3 = st.columns(3)

with purpose_col1:
    st.markdown(
        """
        <div class="info-panel">
            <h3>資料自動化</h3>
            <p>透過 ETL 流程擷取 FinMind 台股日資料，清洗後寫入 PostgreSQL，降低人工整理成本。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with purpose_col2:
    st.markdown(
        """
        <div class="info-panel">
            <h3>量化比較</h3>
            <p>以報酬率、波動率、最大回撤與量能比等指標，建立可比較的因子評分。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with purpose_col3:
    st.markdown(
        """
        <div class="info-panel">
            <h3>視覺化決策輔助</h3>
            <p>使用 Dashboard 呈現最新因子、排行與產業平均，幫助使用者更快掌握市場輪廓。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown('<div class="section-title">使用技術</div>', unsafe_allow_html=True)

tech_col1, tech_col2 = st.columns([1, 1])

with tech_col1:
    st.markdown(
        """
        - **作業環境**：Linux / macOS / Windows
        - **容器化**：Docker、PostgreSQL Container
        - **資料來源**：FinMind API
        - **資料處理**：Python、Pandas、NumPy
        """
    )

with tech_col2:
    st.markdown(
        """
        - **資料庫**：PostgreSQL、SQL Views
        - **量化因子**：20 日報酬、60 日報酬、波動率、最大回撤、量能比、Health Score
        - **視覺化**：Streamlit
        - **環境設定**：python-dotenv、requirements.txt
        """
    )


st.markdown('<div class="section-title">系統架構圖</div>', unsafe_allow_html=True)

architecture = """
digraph {
    graph [rankdir=LR, bgcolor="transparent", pad="0.25", nodesep="0.55", ranksep="0.75"]
    node [shape=box, style="rounded,filled", color="#cbd5e1", fillcolor="#f8fafc", fontname="Arial", fontsize="12", margin="0.14,0.10"]
    edge [color="#64748b", arrowsize="0.8", fontname="Arial", fontsize="10"]

    user [label="使用者\\nStreamlit Dashboard", fillcolor="#ecfeff", color="#67e8f9"]
    api [label="FinMind API\\n台股日資料", fillcolor="#eff6ff", color="#93c5fd"]
    etl [label="stock_etl.py\\n擷取、清洗、入庫", fillcolor="#f0fdf4", color="#86efac"]
    docker [label="Docker\\nPostgreSQL Container", fillcolor="#fefce8", color="#fde047"]
    db [label="PostgreSQL\\nstocks / daily_prices / factor_scores", fillcolor="#fff7ed", color="#fdba74"]
    factors [label="stock_factors.py\\n量化因子計算", fillcolor="#fdf2f8", color="#f9a8d4"]
    views [label="SQL Views\\n最新因子、Top 10、產業平均", fillcolor="#f5f3ff", color="#c4b5fd"]

    api -> etl [label="抓取資料"]
    etl -> docker [label="寫入"]
    docker -> db
    db -> factors [label="讀取股價"]
    factors -> db [label="寫入因子"]
    db -> views [label="整理查詢"]
    views -> user [label="視覺化呈現"]
}
"""

st.graphviz_chart(architecture, use_container_width=True)


st.markdown('<div class="section-title">免責聲明</div>', unsafe_allow_html=True)
st.warning(
    "本平台內容僅供課程專題展示、資料分析練習與研究參考使用，"
    "不構成任何投資建議、買賣推薦或收益保證。股市投資具有風險，"
    "使用者應自行判斷並承擔投資決策結果。"
)


st.markdown('<div class="page-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">因子排行 Top 10</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">根據資料庫最新一日的量化因子，快速比較個股表現與風險特徵。</div>',
    unsafe_allow_html=True,
)

try:
    factors = load_latest_factors()
except Exception as exc:
    st.error("無法讀取資料庫。請確認 Docker PostgreSQL 已啟動，且 .env 連線設定正確。")
    st.code(str(exc))
else:
    if factors.empty:
        st.info("目前 v_latest_factors 沒有資料。請先執行 ETL 與 stock_factors.py 產生因子資料。")
    else:
        latest_date = pd.to_datetime(factors["date"]).max().date()
        st.markdown(
            f"""
            <div class="note">
                目前排行基準日：<strong>{latest_date}</strong>。
                最大回撤以「回撤幅度」由大到小排序，因此數值越負代表歷史跌幅越深。
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab_return_20d, tab_return_60d, tab_volatility, tab_drawdown, tab_volume = st.tabs(
        [
            "20 日報酬率",
            "60 日報酬率",
            "波動率",
            "最大回撤",
            "成交量倍率",
        ]
    )

    with tab_return_20d:
        render_top10("20 日報酬率 Top 10", factors, "return_20d", "20 日報酬率", ascending=False)

    with tab_return_60d:
        render_top10("60 日報酬率 Top 10", factors, "return_60d", "60 日報酬率", ascending=False)

    with tab_volatility:
        render_top10("波動率 Top 10", factors, "volatility_20d", "20 日波動率", ascending=False)

    with tab_drawdown:
        render_top10(
            "最大回撤 Top 10",
            factors,
            "max_drawdown",
            "最大回撤幅度",
            ascending=True,
            use_abs_chart=True,
        )

    with tab_volume:
        render_top10("成交量倍率 Top 10", factors, "volume_ratio", "成交量倍率", ascending=False)


st.markdown('<div class="page-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">個股分析</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">選擇股票代號後，查看收盤價、成交量與最新量化因子摘要。</div>',
    unsafe_allow_html=True,
)

try:
    stocks = load_stocks()
except Exception as exc:
    st.error("無法讀取股票清單。請確認 Docker PostgreSQL 已啟動，且 .env 連線設定正確。")
    st.code(str(exc))
else:
    if stocks.empty:
        st.info("目前 stocks 表沒有資料。請先執行 python3 stock_etl.py --init-db 初始化資料庫。")
    else:
        stock_options = {
            f"{row.stock_id} {row.name}": row.stock_id
            for row in stocks.itertuples(index=False)
        }
        selected_label = st.selectbox("選擇股票代號", list(stock_options.keys()))
        selected_stock_id = stock_options[selected_label]

        prices, selected_factor = load_stock_detail(selected_stock_id)

        if prices.empty:
            st.info("目前這檔股票沒有 daily_prices 資料。請先執行 ETL 更新股價資料。")
        else:
            stock_name = selected_label.split(" ", 1)[1]
            latest_price_date = prices["date"].max().date()
            latest_close = prices.sort_values("date").iloc[-1]["close"]

            header_col1, header_col2, header_col3 = st.columns(3)
            header_col1.metric("股票代號", selected_stock_id)
            header_col2.metric("最新收盤價", f"{latest_close:.2f}")
            header_col3.metric("最新股價日期", str(latest_price_date))

            date_axis = alt.Axis(
                title="日期",
                format="%m/%d",
                labelAngle=0,
                labelOverlap=True,
                tickCount=6,
            )

            price_chart = (
                alt.Chart(prices)
                .mark_line(color="#0f766e", strokeWidth=2)
                .encode(
                    x=alt.X("date:T", axis=date_axis),
                    y=alt.Y("close:Q", title="收盤價", scale=alt.Scale(zero=False)),
                    tooltip=[
                        alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                        alt.Tooltip("close:Q", title="收盤價", format=".2f"),
                    ],
                )
                .properties(height=320)
            )

            volume_chart = (
                alt.Chart(prices)
                .mark_bar(color="#64748b")
                .encode(
                    x=alt.X("date:T", axis=date_axis),
                    y=alt.Y("volume:Q", title="成交量"),
                    tooltip=[
                        alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                        alt.Tooltip("volume:Q", title="成交量", format=",.0f"),
                    ],
                )
                .properties(height=260)
            )

            st.markdown('<div class="section-title">收盤價走勢圖</div>', unsafe_allow_html=True)
            st.altair_chart(price_chart, use_container_width=True)

            st.markdown('<div class="section-title">成交量圖</div>', unsafe_allow_html=True)
            st.altair_chart(volume_chart, use_container_width=True)

            if selected_factor.empty:
                st.info("目前這檔股票沒有最新因子資料。請先執行 python3 stock_factors.py 產生 factor_scores。")
            else:
                factor_row = selected_factor.iloc[0]
                st.markdown('<div class="section-title">最新量化因子</div>', unsafe_allow_html=True)

                metric_row1 = st.columns(4)
                metric_row1[0].metric("20 日報酬率", format_percent(factor_row["return_20d"]))
                metric_row1[1].metric("60 日報酬率", format_percent(factor_row["return_60d"]))
                metric_row1[2].metric("波動率", format_percent(factor_row["volatility_20d"]))
                metric_row1[3].metric("最大回撤", format_percent(factor_row["max_drawdown"]))

                metric_row2 = st.columns(4)
                metric_row2[0].metric("成交量倍率", format_ratio(factor_row["volume_ratio"]))
                metric_row2[1].metric("股票健康分數", format_score(factor_row["health_score"]))
                metric_row2[2].metric("因子日期", str(pd.to_datetime(factor_row["date"]).date()))
                metric_row2[3].metric("產業分類", factor_row["category"])

                st.markdown('<div class="section-title">系統摘要</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="summary-box">{make_system_summary(stock_name, factor_row)}</div>',
                    unsafe_allow_html=True,
                )
