import os

import altair as alt
import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv


st.set_page_config(
    page_title="StockLens | 股票比較",
    page_icon="📊",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background: #f0f4f8; }
    [data-testid="stSidebar"]          { background: #0f172a !important; }
    [data-testid="stSidebar"] *        { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] hr       { border-color: #1e3a5f !important; }

    .block-container { padding: 4.5rem 2rem 3rem; max-width: 1300px; }

    .dash-header {
        display: flex; align-items: center;
        justify-content: space-between; margin-bottom: 1.5rem;
    }
    .dash-title {
        font-size: 1.55rem; font-weight: 800;
        color: #0f172a; letter-spacing: -0.02em;
    }

    .section-hd {
        display: flex; align-items: center; gap: 0.55rem;
        margin: 1.8rem 0 0.8rem;
        font-size: 1.05rem; font-weight: 700; color: #0f172a;
    }
    .section-hd::before {
        content: ""; display: inline-block;
        width: 4px; height: 1.05rem;
        background: #0f766e; border-radius: 2px; flex-shrink: 0;
    }

    /* Stock summary cards */
    .stock-card {
        background: #ffffff; border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,.07);
        padding: 1rem 1.2rem;
        border-top: 4px solid #0f766e;
    }
    .sc-id    { font-size: 0.75rem; font-weight: 700; color: #64748b;
                text-transform: uppercase; letter-spacing: 0.05em; }
    .sc-name  { font-size: 1.05rem; font-weight: 700; color: #0f172a;
                margin: 0.15rem 0; }
    .sc-price { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
    .sc-meta  { font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem; }
    .sc-score-label { font-size: 0.75rem; color: #64748b; margin-top: 0.6rem; }
    .sc-score { font-size: 1.2rem; font-weight: 800; }
    .green  { color: #10b981; }
    .amber  { color: #f59e0b; }
    .red    { color: #ef4444; }

    .note-bar {
        background: #f0fdf4; border: 1px solid #a7f3d0;
        border-left: 4px solid #0f766e; border-radius: 6px;
        padding: 0.6rem 0.9rem; color: #065f46;
        font-size: 0.88rem; margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 StockLens")
    st.markdown("台股量化因子分析平台")
    st.divider()
    st.markdown("**功能區塊**")
    st.markdown(
        """
- 市場概覽
- 因子排行 Top 10
- 個股分析
- **📊 股票比較**
"""
    )
    st.divider()
    st.markdown(
        '<p style="font-size:0.75rem;color:#64748b;">'
        "⚠️ 本平台僅供課程展示與研究參考，不構成投資建議。</p>",
        unsafe_allow_html=True,
    )

# ── DB helpers ────────────────────────────────────────────────────────────────
def get_db_config():
    load_dotenv()
    return {
        "host":     os.getenv("DB_HOST", "localhost"),
        "port":     int(os.getenv("DB_PORT", "5433")),
        "dbname":   os.getenv("DB_NAME", "stockdb"),
        "user":     os.getenv("DB_USER", "stock_user"),
        "password": os.getenv("DB_PASSWORD"),
    }


@st.cache_data(ttl=300)
def load_factors():
    with psycopg2.connect(**get_db_config()) as conn:
        return pd.read_sql(
            """SELECT stock_id, name, category, date, latest_close,
                      return_20d, return_60d, volatility_20d,
                      max_drawdown, volume_ratio, health_score
               FROM v_latest_factors;""",
            conn,
        )


@st.cache_data(ttl=300)
def load_stocks():
    with psycopg2.connect(**get_db_config()) as conn:
        return pd.read_sql(
            "SELECT stock_id, name, category FROM stocks ORDER BY stock_id;",
            conn,
        )


@st.cache_data(ttl=300)
def load_prices_multi(stock_ids: tuple):
    placeholders = ", ".join(["%s"] * len(stock_ids))
    with psycopg2.connect(**get_db_config()) as conn:
        df = pd.read_sql(
            f"SELECT stock_id, date, close FROM daily_prices"
            f" WHERE stock_id IN ({placeholders}) ORDER BY stock_id, date;",
            conn,
            params=stock_ids,
        )
    df["date"] = pd.to_datetime(df["date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df


# ── Helpers ───────────────────────────────────────────────────────────────────
# Up to 5 distinct stock colours
PALETTE = ["#0f766e", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6"]

def fmt_pct(v):   return f"{v * 100:.2f}%" if pd.notna(v) else "—"
def fmt_ratio(v): return f"{v:.2f}x"        if pd.notna(v) else "—"
def fmt_score(v): return f"{v:.1f}"          if pd.notna(v) else "—"

def score_cls(v):
    if pd.isna(v):  return ""
    if v >= 65:     return "green"
    if v >= 45:     return "amber"
    return "red"


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="dash-header">
        <div class="dash-title">📊&nbsp; 股票比較</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Load base data ────────────────────────────────────────────────────────────
try:
    all_factors = load_factors()
    all_stocks  = load_stocks()
except Exception as exc:
    st.error("無法連線至資料庫。請確認 Docker PostgreSQL 已啟動，且 .env 設定正確。")
    st.code(str(exc))
    st.stop()

# ── Stock selector ────────────────────────────────────────────────────────────
options = [
    f"{r.stock_id}　{r.name}"
    for r in all_stocks.itertuples(index=False)
]
option_map = {
    f"{r.stock_id}　{r.name}": r.stock_id
    for r in all_stocks.itertuples(index=False)
}

selected_labels = st.multiselect(
    "選擇 2–5 檔股票進行比較",
    options=options,
    max_selections=5,
    placeholder="請選擇股票…",
)

if len(selected_labels) < 2:
    st.markdown(
        '<div class="note-bar">👆 請至少選擇 <strong>2 檔</strong>股票，最多可選 5 檔。</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Filter factor data ────────────────────────────────────────────────────────
selected_ids = [option_map[lb] for lb in selected_labels]
comp_df = all_factors[all_factors["stock_id"].isin(selected_ids)].copy()
comp_df["label"] = comp_df["stock_id"] + "　" + comp_df["name"]

# Assign a stable colour per stock
color_map = {sid: PALETTE[i] for i, sid in enumerate(selected_ids)}
comp_df["color"] = comp_df["stock_id"].map(color_map)

labels_ordered = [
    comp_df[comp_df["stock_id"] == sid]["label"].values[0]
    for sid in selected_ids
    if sid in comp_df["stock_id"].values
]
color_scale = alt.Scale(domain=labels_ordered, range=[color_map[sid] for sid in selected_ids if sid in comp_df["stock_id"].values])

# ── Stock summary cards ───────────────────────────────────────────────────────
st.markdown('<div class="section-hd">個股摘要</div>', unsafe_allow_html=True)

card_cols = st.columns(len(selected_ids))
for col, sid in zip(card_cols, selected_ids):
    rows = comp_df[comp_df["stock_id"] == sid]
    if rows.empty:
        with col:
            st.warning(f"{sid} 無因子資料")
        continue
    row = rows.iloc[0]
    sc  = score_cls(row["health_score"])
    accent = color_map[sid]

    with col:
        st.markdown(
            f"""
            <div class="stock-card" style="border-top-color:{accent};">
                <div class="sc-id">{row["stock_id"]}　·　{row["category"]}</div>
                <div class="sc-name">{row["name"]}</div>
                <div class="sc-price">{row["latest_close"]:.2f}</div>
                <div class="sc-meta">因子日期：{pd.to_datetime(row["date"]).date()}</div>
                <div class="sc-score-label">Health Score</div>
                <div class="sc-score {sc}">{fmt_score(row["health_score"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── 1. 報酬率比較 ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">報酬率比較</div>', unsafe_allow_html=True)

ret_long = (
    comp_df[["label", "return_20d", "return_60d"]]
    .melt(id_vars="label", value_vars=["return_20d", "return_60d"],
          var_name="period", value_name="return_val")
)
ret_long["return_pct"] = ret_long["return_val"] * 100
ret_long["period"] = ret_long["period"].map({"return_20d": "20 日報酬率", "return_60d": "60 日報酬率"})

ret_chart = (
    alt.Chart(ret_long)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        x=alt.X("period:N", title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("label:N", sort=labels_ordered),
        y=alt.Y("return_pct:Q", title="報酬率 (%)",
                axis=alt.Axis(format=".1f")),
        color=alt.Color("label:N", scale=color_scale,
                        legend=alt.Legend(title="股票", orient="top")),
        tooltip=[
            alt.Tooltip("label:N", title="股票"),
            alt.Tooltip("period:N", title="期間"),
            alt.Tooltip("return_pct:Q", title="報酬率 (%)", format=".2f"),
        ],
    )
    .properties(height=300)
)

# Zero baseline
zero_line = (
    alt.Chart(pd.DataFrame({"y": [0]}))
    .mark_rule(color="#94a3b8", strokeWidth=1)
    .encode(y="y:Q")
)

st.altair_chart(alt.layer(ret_chart, zero_line), use_container_width=True)

# ── 2. 波動率 & 最大回撤 ──────────────────────────────────────────────────────
st.markdown('<div class="section-hd">風險指標比較</div>', unsafe_allow_html=True)

vol_col, dd_col = st.columns(2, gap="medium")

with vol_col:
    vol_df = comp_df.copy()
    vol_df["vol_pct"] = vol_df["volatility_20d"] * 100

    vol_chart = (
        alt.Chart(vol_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("vol_pct:Q", title="20 日波動率 (%)"),
            y=alt.Y("label:N", sort=labels_ordered, title=None),
            color=alt.Color("label:N", scale=color_scale, legend=None),
            tooltip=[
                alt.Tooltip("label:N", title="股票"),
                alt.Tooltip("vol_pct:Q", title="波動率 (%)", format=".2f"),
            ],
        )
        .properties(height=220, title="波動率（越低越穩定）")
    )
    st.altair_chart(vol_chart, use_container_width=True)

with dd_col:
    dd_df = comp_df.copy()
    dd_df["dd_pct"] = dd_df["max_drawdown"].abs() * 100

    dd_chart = (
        alt.Chart(dd_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("dd_pct:Q", title="最大回撤幅度 (%)"),
            y=alt.Y("label:N", sort=labels_ordered, title=None),
            color=alt.Color("label:N", scale=color_scale, legend=None),
            tooltip=[
                alt.Tooltip("label:N", title="股票"),
                alt.Tooltip("dd_pct:Q", title="最大回撤 (%)", format=".2f"),
            ],
        )
        .properties(height=220, title="最大回撤（越低跌幅越小）")
    )
    st.altair_chart(dd_chart, use_container_width=True)

# ── 3. 成交量倍率 & 健康分數 ──────────────────────────────────────────────────
st.markdown('<div class="section-hd">量能 & 綜合評分</div>', unsafe_allow_html=True)

vr_col, hs_col = st.columns(2, gap="medium")

with vr_col:
    vr_chart = (
        alt.Chart(comp_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("volume_ratio:Q", title="成交量倍率（5日均量 / 20日均量）"),
            y=alt.Y("label:N", sort=labels_ordered, title=None),
            color=alt.Color("label:N", scale=color_scale, legend=None),
            tooltip=[
                alt.Tooltip("label:N", title="股票"),
                alt.Tooltip("volume_ratio:Q", title="量能比", format=".2f"),
            ],
        )
        .properties(height=220, title="成交量倍率（>1 代表近期量能放大）")
    )

    ref_line = (
        alt.Chart(pd.DataFrame({"x": [1]}))
        .mark_rule(color="#94a3b8", strokeDash=[4, 3], strokeWidth=1.2)
        .encode(x="x:Q")
    )
    st.altair_chart(alt.layer(vr_chart, ref_line), use_container_width=True)

with hs_col:
    hs_chart = (
        alt.Chart(comp_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("health_score:Q", title="Health Score",
                    scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("label:N", sort=labels_ordered, title=None),
            color=alt.Color(
                "health_score:Q",
                scale=alt.Scale(
                    domain=[0, 50, 100],
                    range=["#ef4444", "#f59e0b", "#10b981"],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("label:N", title="股票"),
                alt.Tooltip("health_score:Q", title="Health Score", format=".2f"),
                alt.Tooltip("category:N", title="產業"),
            ],
        )
        .properties(height=220, title="綜合健康分數（0–100，越高越好）")
    )
    st.altair_chart(hs_chart, use_container_width=True)

# ── 4. 收盤價走勢比較（標準化至 100）────────────────────────────────────────────
st.markdown('<div class="section-hd">收盤價走勢比較</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="font-size:0.82rem;color:#64748b;margin-bottom:0.6rem;">'
    "以各股最早共同交易日為基準設為 100，消除絕對價格差異，方便直接比較漲跌幅。</div>",
    unsafe_allow_html=True,
)

try:
    prices = load_prices_multi(tuple(selected_ids))
except Exception as exc:
    st.warning(f"無法載入股價資料：{exc}")
    prices = pd.DataFrame()

if not prices.empty:
    # Find common start date (latest of each stock's earliest date)
    first_dates = prices.groupby("stock_id")["date"].min()
    common_start = first_dates.max()
    prices = prices[prices["date"] >= common_start].copy()

    # Normalise each stock's price to 100 at common_start
    base = (
        prices[prices["date"] == common_start]
        .set_index("stock_id")["close"]
        .rename("base_close")
    )
    prices = prices.join(base, on="stock_id")
    prices["norm"] = prices["close"] / prices["base_close"] * 100
    prices["label"] = prices["stock_id"].map(
        {sid: comp_df[comp_df["stock_id"] == sid]["label"].values[0]
         for sid in selected_ids if sid in comp_df["stock_id"].values}
    )

    trend_chart = (
        alt.Chart(prices.dropna(subset=["norm", "label"]))
        .mark_line(strokeWidth=2.2)
        .encode(
            x=alt.X("date:T", title="日期",
                    axis=alt.Axis(format="%m/%d", labelAngle=0, tickCount=6)),
            y=alt.Y("norm:Q", title="相對指數（起始=100）",
                    scale=alt.Scale(zero=False)),
            color=alt.Color("label:N", scale=color_scale,
                            legend=alt.Legend(title="股票", orient="top")),
            tooltip=[
                alt.Tooltip("label:N", title="股票"),
                alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                alt.Tooltip("close:Q", title="收盤價", format=".2f"),
                alt.Tooltip("norm:Q", title="相對指數", format=".1f"),
            ],
        )
        .properties(height=340)
        .interactive()
    )

    base_line = (
        alt.Chart(pd.DataFrame({"y": [100]}))
        .mark_rule(color="#94a3b8", strokeDash=[4, 3], strokeWidth=1)
        .encode(y="y:Q")
    )

    st.altair_chart(alt.layer(trend_chart, base_line), use_container_width=True)
else:
    st.info("無法載入股價走勢資料，請確認 daily_prices 表有資料。")
