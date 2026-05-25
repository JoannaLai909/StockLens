import os

import altair as alt
import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv


st.set_page_config(
    page_title="StockLens | 台股量化分析",
    page_icon="📈",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Background */
    [data-testid="stAppViewContainer"] { background: #f0f4f8; }
    [data-testid="stSidebar"]          { background: #0f172a !important; }
    [data-testid="stSidebar"] *        { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] a        { color: #7dd3fc !important; }
    [data-testid="stSidebar"] hr       { border-color: #1e3a5f !important; }
    [data-testid="stSidebar"] .stExpander summary { color: #94a3b8 !important; }

    .block-container { padding: 4.5rem 2rem 3rem; max-width: 1300px; }

    /* Dashboard title row */
    .dash-header {
        display: flex; align-items: center;
        justify-content: space-between; margin-bottom: 1.3rem;
        padding-left: 0.25rem;
    }
    .dash-title {
        font-size: 1.55rem; font-weight: 800;
        color: #0f172a; letter-spacing: -0.02em;
    }
    .dash-badge {
        font-size: 0.8rem; color: #64748b;
        background: #e2e8f0; padding: 0.3rem 0.8rem;
        border-radius: 99px;
    }

    /* KPI cards */
    .kpi-card {
        background: #ffffff; border-radius: 12px;
        padding: 1.1rem 1.3rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,.07);
        position: relative; overflow: hidden;
    }
    .kpi-card::before {
        content: ""; position: absolute;
        left: 0; top: 0; bottom: 0; width: 4px;
        background: #0f766e;
        border-radius: 12px 0 0 12px;
    }
    .kpi-card.red::before   { background: #ef4444; }
    .kpi-card.amber::before { background: #f59e0b; }
    .kpi-card.green::before { background: #10b981; }
    .kpi-label {
        font-size: 0.72rem; font-weight: 700;
        color: #64748b; text-transform: uppercase;
        letter-spacing: 0.06em; margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.9rem; font-weight: 800;
        color: #0f172a; line-height: 1.1;
    }
    .kpi-sub { font-size: 0.8rem; color: #94a3b8; margin-top: 0.15rem; }

    /* Section headers */
    .section-hd {
        display: flex; align-items: center; gap: 0.55rem;
        margin: 2rem 0 0.85rem;
        font-size: 1.08rem; font-weight: 700; color: #0f172a;
    }
    .section-hd::before {
        content: ""; display: inline-block;
        width: 4px; height: 1.05rem;
        background: #0f766e; border-radius: 2px;
        flex-shrink: 0;
    }
    .section-sub {
        color: #64748b; font-size: 0.88rem;
        margin: -0.5rem 0 0.85rem;
    }

    /* Note bar */
    .note-bar {
        background: #f0fdf4; border: 1px solid #a7f3d0;
        border-left: 4px solid #0f766e; border-radius: 6px;
        padding: 0.6rem 0.9rem; color: #065f46;
        font-size: 0.88rem; margin-bottom: 0.9rem;
    }

    /* Stock header */
    .stock-hd {
        background: linear-gradient(135deg, #0f172a 0%, #134e4a 100%);
        border-radius: 12px; padding: 1.25rem 1.6rem;
        margin-bottom: 1.1rem;
    }
    .stock-hd-name  { color: #fff; font-size: 1.4rem; font-weight: 800; margin: 0 0 0.25rem; }
    .stock-hd-price { color: #94a3b8; font-size: 0.9rem; }
    .stock-hd-price strong { color: #fff; font-size: 1.5rem; }
    .price-up   { color: #34d399; }
    .price-down { color: #f87171; }

    /* Summary box */
    .summary-box {
        background: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 10px; padding: 1rem 1.2rem;
        color: #334155; line-height: 1.85;
        box-shadow: 0 1px 3px rgba(0,0,0,.05);
    }

    /* Health badge */
    .hb-g { background:#d1fae5; color:#065f46; padding:2px 9px; border-radius:99px; font-size:0.82rem; font-weight:700; }
    .hb-a { background:#fef3c7; color:#92400e; padding:2px 9px; border-radius:99px; font-size:0.82rem; font-weight:700; }
    .hb-r { background:#fee2e2; color:#991b1b; padding:2px 9px; border-radius:99px; font-size:0.82rem; font-weight:700; }

    /* Sidebar disclaimer */
    .sidebar-disc { font-size:0.75rem; color:#64748b; line-height:1.6; }
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
- 市場概覽（散佈圖 + 產業比較）
- 因子排行 Top 10
- 個股分析
"""
    )
    st.divider()

    with st.expander("量化因子說明"):
        st.markdown(
            """
| 因子 | 說明 |
|------|------|
| return_20d | 近 20 日報酬率 |
| return_60d | 近 60 日報酬率 |
| volatility | 20 日收益標準差 |
| max_drawdown | 60 日最大回撤 |
| volume_ratio | 5日/20日均量比 |
| health_score | 綜合健康分數 0–100 |
"""
        )

    with st.expander("使用技術"):
        st.markdown(
            """
**資料來源** FinMind API
**資料庫** PostgreSQL + Docker
**後端** Python · Pandas · NumPy
**前端** Streamlit · Altair
**環境** python-dotenv
"""
        )

    st.divider()
    st.markdown(
        '<p class="sidebar-disc">⚠️ 本平台僅供課程展示與研究參考，'
        "不構成任何投資建議或收益保證。</p>",
        unsafe_allow_html=True,
    )


# ── DB helpers ────────────────────────────────────────────────────────────────
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
        SELECT stock_id, name, category, date, latest_close,
               return_20d, return_60d, volatility_20d,
               max_drawdown, volume_ratio, health_score
        FROM v_latest_factors;
    """
    with psycopg2.connect(**get_db_config()) as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def load_industry_avg():
    query = """
        SELECT category, stock_count, avg_return_20d,
               avg_return_60d, avg_volatility, avg_health_score
        FROM v_industry_avg
        ORDER BY avg_health_score DESC NULLS LAST;
    """
    with psycopg2.connect(**get_db_config()) as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def load_stocks():
    with psycopg2.connect(**get_db_config()) as conn:
        return pd.read_sql(
            "SELECT stock_id, name, category FROM stocks ORDER BY stock_id;",
            conn,
        )


@st.cache_data(ttl=300)
def load_stock_detail(stock_id):
    with psycopg2.connect(**get_db_config()) as conn:
        prices = pd.read_sql(
            "SELECT date, close, volume FROM daily_prices"
            " WHERE stock_id=%s ORDER BY date;",
            conn,
            params=(stock_id,),
        )
        factor = pd.read_sql(
            """SELECT stock_id, name, category, date, latest_close,
                      return_20d, return_60d, volatility_20d,
                      max_drawdown, volume_ratio, health_score
               FROM v_latest_factors WHERE stock_id=%s;""",
            conn,
            params=(stock_id,),
        )
    if not prices.empty:
        prices["date"] = pd.to_datetime(prices["date"])
        prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
        prices["volume"] = pd.to_numeric(prices["volume"], errors="coerce")
    return prices, factor


# ── Formatters ────────────────────────────────────────────────────────────────
def fmt_pct(v):
    return f"{v * 100:.2f}%" if pd.notna(v) else "—"


def fmt_ratio(v):
    return f"{v:.2f}x" if pd.notna(v) else "—"


def fmt_score(v):
    return f"{v:.2f}" if pd.notna(v) else "—"


def health_color(score):
    if pd.isna(score):
        return "#94a3b8"
    if score >= 65:
        return "#10b981"
    if score >= 45:
        return "#f59e0b"
    return "#ef4444"


def make_summary(stock_name, row):
    health = row["health_score"]
    r20, r60 = row["return_20d"], row["return_60d"]
    vol, dd = row["volatility_20d"], row["max_drawdown"]
    vr = row["volume_ratio"]

    if pd.isna(health):
        hc = "目前健康分數不足，建議先補齊資料後再判讀。"
    elif health >= 70:
        hc = "整體健康分數偏高，近期量化表現相對穩健。"
    elif health >= 50:
        hc = "整體健康分數位於中段，仍需搭配風險指標觀察。"
    else:
        hc = "整體健康分數偏低，近期風險或表現可能較不理想。"

    tc = "短中期報酬率訊號尚不明確。"
    if pd.notna(r20) and pd.notna(r60):
        if r20 > 0 and r60 > 0:
            tc = "20 日與 60 日報酬率皆為正，短中期走勢偏強。"
        elif r20 < 0 and r60 < 0:
            tc = "20 日與 60 日報酬率皆為負，短中期走勢偏弱。"
        elif r20 > r60:
            tc = "20 日報酬率優於 60 日報酬率，近期動能有轉強跡象。"

    rc = "風險指標資料不足。"
    if pd.notna(vol) and pd.notna(dd):
        rc = f"20 日波動率 {fmt_pct(vol)}，最大回撤 {fmt_pct(dd)}。"

    vc = "成交量倍率資料不足。"
    if pd.notna(vr):
        if vr >= 1.2:
            vc = f"成交量倍率 {fmt_ratio(vr)}，近期量能高於 20 日均量。"
        elif vr <= 0.8:
            vc = f"成交量倍率 {fmt_ratio(vr)}，近期量能低於 20 日均量。"
        else:
            vc = f"成交量倍率 {fmt_ratio(vr)}，近期量能接近 20 日均量。"

    return f"{stock_name}：{hc} {tc} {rc} {vc}"


# ── Top-10 renderer ───────────────────────────────────────────────────────────
def _fmt_table(df, metric_col):
    t = df.copy()
    t.insert(0, "名次", range(1, len(t) + 1))
    for c in ["return_20d", "return_60d", "volatility_20d", "max_drawdown"]:
        if c in t.columns:
            t[c] = t[c].apply(lambda v: f"{v * 100:.2f}%" if pd.notna(v) else "—")
    if "volume_ratio" in t.columns:
        t["volume_ratio"] = t["volume_ratio"].apply(
            lambda v: f"{v:.2f}x" if pd.notna(v) else "—"
        )
    if "latest_close" in t.columns:
        t["latest_close"] = t["latest_close"].apply(
            lambda v: f"{v:.2f}" if pd.notna(v) else "—"
        )
    if "health_score" in t.columns:
        t["health_score"] = t["health_score"].apply(
            lambda v: f"{v:.2f}" if pd.notna(v) else "—"
        )
    cols = ["名次", "stock_id", "name", "category", "latest_close", metric_col, "health_score"]
    return t[[c for c in cols if c in t.columns]]


def render_top10(df, metric_col, label, ascending=False, use_abs=False):
    ranked = (
        df.dropna(subset=[metric_col])
        .sort_values(metric_col, ascending=ascending)
        .head(10)
        .copy()
    )
    if ranked.empty:
        st.info("目前資料不足，無法顯示此排行榜。")
        return

    chart_df = ranked.copy()
    chart_df["_label"] = chart_df["stock_id"] + " " + chart_df["name"]
    chart_df["_val"] = chart_df[metric_col].abs() if use_abs else chart_df[metric_col]

    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("_val:Q", title=label),
            y=alt.Y("_label:N", sort="-x", title=None),
            color=alt.Color(
                "health_score:Q",
                scale=alt.Scale(
                    domain=[0, 50, 100], range=["#ef4444", "#f59e0b", "#10b981"]
                ),
                legend=alt.Legend(title="Health"),
            ),
            tooltip=[
                alt.Tooltip("stock_id:N", title="代號"),
                alt.Tooltip("name:N", title="名稱"),
                alt.Tooltip(f"{metric_col}:Q", title=label, format=".4f"),
                alt.Tooltip("health_score:Q", title="Health Score", format=".2f"),
            ],
        )
        .properties(height=300)
    )

    tc, cc = st.columns([1.1, 1])
    with tc:
        st.dataframe(_fmt_table(ranked, metric_col), use_container_width=True, hide_index=True)
    with cc:
        st.altair_chart(chart, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

# ── Load data ─────────────────────────────────────────────────────────────────
factors = pd.DataFrame()
industry = pd.DataFrame()
db_error = None

try:
    factors = load_latest_factors()
    industry = load_industry_avg()
except Exception as exc:
    db_error = exc

# ── Page header ───────────────────────────────────────────────────────────────
today_str = pd.Timestamp.now().strftime("%Y/%m/%d %H:%M")
st.markdown(
    f"""
    <div class="dash-header">
        <div class="dash-title">📈&nbsp; StockLens — 台股量化因子分析儀表板</div>
        <div class="dash-badge">資料更新：{today_str}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if db_error is not None:
    st.error(
        "無法連線至資料庫。請確認 Docker PostgreSQL 已啟動，且 .env 連線設定正確。"
    )
    st.code(str(db_error))
    st.stop()

# ── KPI strip ─────────────────────────────────────────────────────────────────
n_stocks = len(factors) if not factors.empty else 0
data_date = (
    pd.to_datetime(factors["date"]).max().date() if not factors.empty else "—"
)
avg_health = factors["health_score"].mean() if not factors.empty else None
top_row = (
    factors.nlargest(1, "health_score").iloc[0]
    if not factors.empty and not factors["health_score"].isna().all()
    else None
)

# Pick accent colour for avg health card
health_cls = ""
if avg_health is not None:
    health_cls = "green" if avg_health >= 65 else ("amber" if avg_health >= 45 else "red")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">監控股票數</div>
            <div class="kpi-value">{n_stocks}</div>
            <div class="kpi-sub">支股票</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">資料基準日</div>
            <div class="kpi-value" style="font-size:1.35rem;">{data_date}</div>
            <div class="kpi-sub">最新因子計算日</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi3:
    avg_display = f"{avg_health:.1f}" if avg_health is not None else "—"
    st.markdown(
        f"""
        <div class="kpi-card {health_cls}">
            <div class="kpi-label">平均 Health Score</div>
            <div class="kpi-value">{avg_display}</div>
            <div class="kpi-sub">所有股票平均（0–100）</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi4:
    if top_row is not None:
        top_label = f"{top_row['stock_id']} {top_row['name']}"
        top_score = f"{top_row['health_score']:.1f} 分"
    else:
        top_label, top_score = "—", "—"
    st.markdown(
        f"""
        <div class="kpi-card green">
            <div class="kpi-label">最高分個股</div>
            <div class="kpi-value" style="font-size:1.3rem;">{top_label}</div>
            <div class="kpi-sub">Health Score {top_score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Market Overview ───────────────────────────────────────────────────────────
if not factors.empty:
    st.markdown('<div class="section-hd">市場概覽</div>', unsafe_allow_html=True)

    # Quadrant legend guide
    st.markdown(
        """
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;margin-bottom:1rem;">
          <div style="background:rgba(16,185,129,0.1);border:1px solid #a7f3d0;border-left:3px solid #10b981;border-radius:8px;padding:0.55rem 0.8rem;">
            <div style="font-weight:700;color:#065f46;font-size:0.82rem;">右下 ✓ 理想區</div>
            <div style="font-size:0.78rem;color:#374151;">高報酬 · 低波動</div>
          </div>
          <div style="background:rgba(245,158,11,0.08);border:1px solid #fde68a;border-left:3px solid #f59e0b;border-radius:8px;padding:0.55rem 0.8rem;">
            <div style="font-weight:700;color:#92400e;font-size:0.82rem;">右上 ⚠ 積極區</div>
            <div style="font-size:0.78rem;color:#374151;">高報酬 · 高波動</div>
          </div>
          <div style="background:rgba(148,163,184,0.1);border:1px solid #e2e8f0;border-left:3px solid #94a3b8;border-radius:8px;padding:0.55rem 0.8rem;">
            <div style="font-weight:700;color:#475569;font-size:0.82rem;">左下 　觀望區</div>
            <div style="font-size:0.78rem;color:#374151;">低報酬 · 低波動</div>
          </div>
          <div style="background:rgba(239,68,68,0.07);border:1px solid #fecaca;border-left:3px solid #ef4444;border-radius:8px;padding:0.55rem 0.8rem;">
            <div style="font-weight:700;color:#991b1b;font-size:0.82rem;">左上 ✗ 迴避區</div>
            <div style="font-size:0.78rem;color:#374151;">低報酬 · 高波動</div>
          </div>
        </div>
        <div style="font-size:0.8rem;color:#64748b;margin-bottom:0.8rem;">
          泡泡大小代表成交量倍率（越大代表量能越強），顏色代表 Health Score（綠＝健康、紅＝偏弱）
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.6, 1], gap="medium")

    with left_col:
        scatter_df = factors.dropna(subset=["return_20d", "volatility_20d"]).copy()
        scatter_df["_label"] = scatter_df["stock_id"] + " " + scatter_df["name"]
        scatter_df["_r20"] = scatter_df["return_20d"] * 100
        scatter_df["_vol"] = scatter_df["volatility_20d"] * 100

        # Compute axis ranges with padding
        r_pad = (scatter_df["_r20"].max() - scatter_df["_r20"].min()) * 0.12 or 1
        v_pad = (scatter_df["_vol"].max() - scatter_df["_vol"].min()) * 0.12 or 0.5
        x_min = scatter_df["_r20"].min() - r_pad
        x_max = scatter_df["_r20"].max() + r_pad
        y_min = max(scatter_df["_vol"].min() - v_pad, 0)
        y_max = scatter_df["_vol"].max() + v_pad
        med_v = float(scatter_df["_vol"].median())

        # Quadrant background shading
        quad_data = pd.DataFrame([
            {"x1": 0,     "x2": x_max, "y1": y_min,  "y2": med_v, "zone": "理想"},
            {"x1": 0,     "x2": x_max, "y1": med_v,  "y2": y_max, "zone": "積極"},
            {"x1": x_min, "x2": 0,     "y1": y_min,  "y2": med_v, "zone": "觀望"},
            {"x1": x_min, "x2": 0,     "y1": med_v,  "y2": y_max, "zone": "迴避"},
        ])
        bg = (
            alt.Chart(quad_data)
            .mark_rect(opacity=0.07)
            .encode(
                x=alt.X("x1:Q", scale=alt.Scale(domain=[x_min, x_max])),
                x2="x2:Q",
                y=alt.Y("y1:Q", scale=alt.Scale(domain=[y_min, y_max])),
                y2="y2:Q",
                color=alt.Color(
                    "zone:N",
                    scale=alt.Scale(
                        domain=["理想", "積極", "觀望", "迴避"],
                        range=["#10b981", "#f59e0b", "#94a3b8", "#ef4444"],
                    ),
                    legend=None,
                ),
            )
        )

        # Divider lines at x=0 and y=median volatility
        vline = (
            alt.Chart(pd.DataFrame({"x": [0]}))
            .mark_rule(color="#64748b", strokeDash=[5, 4], strokeWidth=1.2)
            .encode(x="x:Q")
        )
        hline = (
            alt.Chart(pd.DataFrame({"y": [med_v]}))
            .mark_rule(color="#64748b", strokeDash=[5, 4], strokeWidth=1.2)
            .encode(y="y:Q")
        )

        # Data points
        points = (
            alt.Chart(scatter_df)
            .mark_circle(opacity=0.88, stroke="white", strokeWidth=0.8)
            .encode(
                x=alt.X(
                    "_r20:Q",
                    title="20 日報酬率 (%)",
                    scale=alt.Scale(domain=[x_min, x_max]),
                    axis=alt.Axis(titleFontSize=12),
                ),
                y=alt.Y(
                    "_vol:Q",
                    title="20 日波動率 (%)",
                    scale=alt.Scale(domain=[y_min, y_max]),
                    axis=alt.Axis(titleFontSize=12),
                ),
                size=alt.Size(
                    "volume_ratio:Q",
                    scale=alt.Scale(range=[60, 400]),
                    legend=None,
                ),
                color=alt.Color(
                    "health_score:Q",
                    scale=alt.Scale(
                        domain=[0, 50, 100],
                        range=["#ef4444", "#f59e0b", "#10b981"],
                    ),
                    legend=alt.Legend(
                        title="Health Score",
                        orient="top-right",
                        direction="horizontal",
                        gradientLength=120,
                        titleFontSize=11,
                        labelFontSize=10,
                    ),
                ),
                tooltip=[
                    alt.Tooltip("_label:N", title="股票"),
                    alt.Tooltip("_r20:Q", title="20日報酬(%)", format=".2f"),
                    alt.Tooltip("_vol:Q", title="波動率(%)", format=".2f"),
                    alt.Tooltip("volume_ratio:Q", title="量能比", format=".2f"),
                    alt.Tooltip("health_score:Q", title="Health Score", format=".1f"),
                    alt.Tooltip("category:N", title="產業"),
                ],
            )
        )

        scatter = (
            alt.layer(bg, vline, hline, points)
            .resolve_scale(color="independent")
            .properties(height=380, title="報酬率 vs 波動率（右下角為最理想）")
            .interactive()
        )
        st.altair_chart(scatter, use_container_width=True)

    with right_col:
        if not industry.empty:
            ind_chart = (
                alt.Chart(industry)
                .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    x=alt.X(
                        "avg_health_score:Q",
                        title="平均 Health Score（0–100）",
                        scale=alt.Scale(domain=[0, 100]),
                    ),
                    y=alt.Y("category:N", sort="-x", title=None),
                    color=alt.Color(
                        "avg_health_score:Q",
                        scale=alt.Scale(
                            domain=[0, 50, 100],
                            range=["#ef4444", "#f59e0b", "#10b981"],
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("category:N", title="產業"),
                        alt.Tooltip("avg_health_score:Q", title="平均 Health Score", format=".1f"),
                        alt.Tooltip("avg_return_20d:Q", title="平均 20日報酬", format=".2%"),
                        alt.Tooltip("avg_volatility:Q", title="平均波動率", format=".2%"),
                        alt.Tooltip("stock_count:Q", title="涵蓋股票數"),
                    ],
                )
                .properties(height=380, title="各產業平均健康分數")
            )
            st.altair_chart(ind_chart, use_container_width=True)
        else:
            st.info("產業平均資料不足，請確認 v_industry_avg 有資料。")

# ── Factor Rankings ───────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">因子排行 Top 10</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">根據最新一日量化因子快速比較個股表現與風險特徵</div>',
    unsafe_allow_html=True,
)

if factors.empty:
    st.info("目前 v_latest_factors 沒有資料。請先執行 ETL 與 stock_factors.py。")
else:
    latest_date = pd.to_datetime(factors["date"]).max().date()
    st.markdown(
        f'<div class="note-bar">資料基準日：<strong>{latest_date}</strong>　·　'
        "最大回撤以回撤幅度由大到小排序，數值越負代表歷史跌幅越深。</div>",
        unsafe_allow_html=True,
    )

    tab_r20, tab_r60, tab_vol, tab_dd, tab_vr = st.tabs(
        ["20 日報酬率", "60 日報酬率", "波動率", "最大回撤", "成交量倍率"]
    )
    with tab_r20:
        render_top10(factors, "return_20d", "20 日報酬率", ascending=False)
    with tab_r60:
        render_top10(factors, "return_60d", "60 日報酬率", ascending=False)
    with tab_vol:
        render_top10(factors, "volatility_20d", "20 日波動率", ascending=False)
    with tab_dd:
        render_top10(factors, "max_drawdown", "最大回撤幅度", ascending=True, use_abs=True)
    with tab_vr:
        render_top10(factors, "volume_ratio", "成交量倍率", ascending=False)

# ── Stock Analyzer ────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">個股分析</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">選擇股票後查看收盤價走勢、成交量與最新量化因子摘要</div>',
    unsafe_allow_html=True,
)

try:
    stocks = load_stocks()
except Exception as exc:
    st.error("無法讀取股票清單。")
    st.code(str(exc))
    stocks = pd.DataFrame()

if not stocks.empty:
    options = {
        f"{r.stock_id}　{r.name}": r.stock_id
        for r in stocks.itertuples(index=False)
    }
    selected_label = st.selectbox("選擇股票代號", list(options.keys()))
    sid = options[selected_label]
    stock_name = selected_label.split("　", 1)[1]

    prices, sel_factor = load_stock_detail(sid)

    if prices.empty:
        st.info("此股票目前沒有 daily_prices 資料。請先執行 ETL 更新股價。")
    else:
        latest_close = prices.sort_values("date").iloc[-1]["close"]
        prev_close = (
            prices.sort_values("date").iloc[-2]["close"]
            if len(prices) > 1
            else latest_close
        )
        delta = latest_close - prev_close
        arrow = "▲" if delta >= 0 else "▼"
        delta_cls = "price-up" if delta >= 0 else "price-down"

        st.markdown(
            f"""
            <div class="stock-hd">
                <div class="stock-hd-name">{sid}　{stock_name}</div>
                <div class="stock-hd-price">
                    收盤價 <strong>{latest_close:.2f}</strong>&ensp;
                    <span class="{delta_cls}">{arrow} {abs(delta):.2f}</span>
                    &ensp;·&ensp; 最新日期：{prices["date"].max().date()}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        date_axis = alt.Axis(
            title="日期", format="%m/%d",
            labelAngle=0, labelOverlap=True, tickCount=6,
        )

        price_chart = (
            alt.Chart(prices)
            .mark_line(color="#0f766e", strokeWidth=2.2)
            .encode(
                x=alt.X("date:T", axis=date_axis),
                y=alt.Y("close:Q", title="收盤價", scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                    alt.Tooltip("close:Q", title="收盤價", format=".2f"),
                ],
            )
            .properties(height=300, title=f"{sid} 收盤價走勢")
        )

        volume_chart = (
            alt.Chart(prices)
            .mark_bar(color="#64748b", opacity=0.75)
            .encode(
                x=alt.X("date:T", axis=date_axis),
                y=alt.Y("volume:Q", title="成交量"),
                tooltip=[
                    alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                    alt.Tooltip("volume:Q", title="成交量", format=",.0f"),
                ],
            )
            .properties(height=220, title="成交量")
        )

        pc, vc = st.columns([1.5, 1])
        with pc:
            st.altair_chart(price_chart, use_container_width=True)
        with vc:
            st.altair_chart(volume_chart, use_container_width=True)

        if not sel_factor.empty:
            row = sel_factor.iloc[0]
            st.markdown("**最新量化因子**")
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("20 日報酬率", fmt_pct(row["return_20d"]))
            m2.metric("60 日報酬率", fmt_pct(row["return_60d"]))
            m3.metric("波動率", fmt_pct(row["volatility_20d"]))
            m4.metric("最大回撤", fmt_pct(row["max_drawdown"]))
            m5.metric("量能比", fmt_ratio(row["volume_ratio"]))
            m6.metric("Health Score", fmt_score(row["health_score"]))

            st.markdown(
                f'<div class="summary-box">{make_summary(stock_name, row)}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("此股票目前沒有最新因子資料。請先執行 python3 stock_factors.py。")
