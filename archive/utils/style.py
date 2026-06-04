"""utils/style.py — 全站共用 CSS、sidebar、卡片元件"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from utils.formatters import pct, number, ratio, metric_class

# ── 全站 CSS ─────────────────────────────────────────────────────────────────
PAGE_CSS = """
<style>
:root {
    --bg:     #f0f4f9;
    --card:   #ffffff;
    --border: #dbe4ef;
    --blue:   #0f6fe8;
    --green:  #149b55;
    --red:    #ef4444;
    --orange: #f59e0b;
    --text:   #0b1f3f;
    --muted:  #5d6d86;
}

/* ── 背景 ── */
[data-testid="stAppViewContainer"] { background: var(--bg); }
[data-testid="stHeader"]            { background: transparent; }
.block-container { max-width: 1360px; padding: 1.6rem 2rem 3rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #dce6f2;
    box-shadow: 4px 0 16px rgba(13,38,74,.05);
}
[data-testid="stSidebarNav"] { display: none; }
[data-testid="stSidebar"] .block-container { padding: 1.2rem .9rem 1rem; }

.sl-logo {
    display: flex; align-items: center; gap: .7rem;
    padding: .6rem .5rem 1rem;
    border-bottom: 1px solid #eaf0f8;
    margin-bottom: .6rem;
}
.sl-logo-mark {
    width: 38px; height: 38px; border-radius: 10px; flex-shrink: 0;
    display: grid; place-items: center;
    background: linear-gradient(135deg,#e8f2ff,#e8f7ef);
    color: var(--blue); font-size: 1.15rem; font-weight: 900;
}
.sl-logo-text { font-size: .95rem; font-weight: 800; color: #0b1f3f; line-height:1.2; }
.sl-logo-sub  { font-size: .72rem; color: var(--muted); }

.nav-item {
    display: flex; align-items: center; gap: .65rem;
    padding: .72rem .85rem; margin: .18rem 0;
    border-radius: 8px; cursor: pointer;
    color: #334155; font-weight: 600; font-size: .9rem;
    text-decoration: none; transition: background .15s;
}
.nav-item:hover  { background: #f1f5fb; }
.nav-item.active { background: #e8f2ff; color: var(--blue); font-weight: 700; }
.nav-icon { font-size: 1rem; width: 20px; text-align: center; }

.sidebar-footer {
    margin-top: 1.5rem; padding-top: .9rem;
    border-top: 1px solid #eaf0f8;
    color: var(--muted); font-size: .75rem; line-height: 1.8;
}

/* ── 頁面標題 ── */
.page-header {
    display: flex; align-items: flex-start;
    justify-content: space-between; gap: 1rem;
    margin-bottom: 1.4rem;
}
.page-title   { font-size: 1.75rem; font-weight: 900; color: #061a3a; margin:0; }
.page-sub     { color: var(--muted); font-size: .9rem; margin-top: .3rem; }
.page-updated { color: #334155; font-size: .85rem; white-space: nowrap; padding-top:.4rem; }

/* ── 卡片 ── */
.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(13,38,74,.06);
    padding: 1.1rem 1.25rem;
}
.card-title {
    font-size: .95rem; font-weight: 800; color: #10284a;
    margin-bottom: .7rem; display: flex; align-items: center; gap: .4rem;
}
.card-title .info-dot {
    width: 15px; height: 15px; border-radius: 50%;
    border: 1px solid #8da2bf; color: #6b7d96;
    display: inline-grid; place-items: center;
    font-size: .68rem; font-weight: 800;
}

/* ── KPI 卡片 ── */
.kpi-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(13,38,74,.06);
    padding: 1rem 1.1rem;
    display: flex; align-items: center; gap: .85rem;
}
.kpi-icon {
    width: 48px; height: 48px; border-radius: 12px;
    display: grid; place-items: center;
    font-size: 1.4rem; flex-shrink: 0;
}
.kpi-icon.blue  { background: #e8f2ff; color: var(--blue); }
.kpi-icon.green { background: #e8f7ef; color: var(--green); }
.kpi-label { font-size: .8rem; font-weight: 700; color: var(--muted); margin-bottom: .2rem; }
.kpi-value { font-size: 1.55rem; font-weight: 900; line-height: 1; }
.kpi-value.blue  { color: var(--blue); }
.kpi-value.green { color: var(--green); }
.kpi-sub   { font-size: .78rem; color: var(--muted); margin-top: .25rem; }
.pill {
    display: inline-flex; align-items: center;
    border-radius: 6px; padding: .22rem .5rem;
    background: #dff3e8; color: var(--green);
    font-weight: 800; font-size: .8rem; margin-left: .45rem;
}

/* ── 個股快速分析 ── */
.stock-info-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: .9rem 1rem;
}
.stock-id-badge {
    font-size: .78rem; font-weight: 800; color: var(--blue);
    background: #e8f2ff; border-radius: 6px;
    padding: .2rem .5rem; display: inline-block; margin-bottom: .4rem;
}
.stock-name  { font-size: 1.1rem; font-weight: 800; color: #0b1f3f; margin-bottom: .5rem; }
.stock-meta  { font-size: .82rem; color: var(--muted); line-height: 2; }

.metric-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: .75rem .85rem; text-align: center;
}
.metric-label { font-size: .75rem; font-weight: 700; color: var(--muted); margin-bottom: .35rem; }
.metric-value { font-size: 1.05rem; font-weight: 900; }

.score-card {
    background: #effaf4; border: 1px solid #c6e8d4;
    border-radius: 10px; padding: .75rem .85rem;
}
.cluster-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: .75rem .85rem;
}

/* ── 排行 Tab ── */
.rank-section-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: .5rem;
}
.rank-section-title { font-size: 1rem; font-weight: 800; color: #10284a; }

/* ── 色彩工具 ── */
.positive { color: var(--green); font-weight: 800; }
.negative { color: var(--red);   font-weight: 800; }
.blue-text   { color: var(--blue);   font-weight: 800; }
.orange-text { color: var(--orange); font-weight: 800; }

/* ── 下載按鈕 ── */
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg,#0f6fe8,#0960cf);
    color: white; font-weight: 800; border: 0; border-radius: 10px;
    box-shadow: 0 6px 16px rgba(15,111,232,.25);
    padding: .65rem 1.4rem; font-size: .92rem;
}
div[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg,#0b63d8,#0757bd); color: white;
}
</style>
"""

# ── 排行表 iframe CSS ────────────────────────────────────────────────────────
RANKING_CSS = """
<style>
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:transparent; }
.rank-grid { display:grid; grid-template-columns:1fr 1fr; border-top:1px solid #eef3f8; }
.rank-table { width:100%; border-collapse:collapse; color:#122844; font-size:.84rem; }
.rank-table th { color:#304461; background:#f5f9fd; padding:.48rem .5rem;
                 font-weight:800; border-bottom:1px solid #dbe4ef; text-align:left; }
.rank-table td { padding:.46rem .5rem; border-bottom:1px solid #eef3f8; vertical-align:middle; }
.rank-table .num { text-align:center; font-weight:800; color:#64748b; }
.rank-table.right { border-left:1px solid #dbe4ef; }
.bar-bg  { height:6px; border-radius:99px; background:#e9eef5; overflow:hidden; min-width:70px; }
.bar-fill{ height:100%; border-radius:99px; background:linear-gradient(90deg,#2fb86a,#54bf78); }
.positive { color:#149b55; font-weight:800; }
.negative { color:#ef4444; font-weight:800; }
.blue-text   { color:#0f6fe8; font-weight:800; }
.orange-text { color:#f59e0b; font-weight:800; }
</style>
"""


def inject_css():
    st.markdown(PAGE_CSS, unsafe_allow_html=True)


def render_sidebar(active: str = "home"):
    """
    active: "home" | "ranking" | "stock" | "compare" | "health"
    """
    pages = [
        ("home",    "◆", "市場概覽",   "app"),
        ("ranking", "≡", "因子排行",   "pages/1_因子排行"),
        ("stock",   "◎", "個股分析",   "pages/2_個股分析"),
        ("compare", "⇌", "股票比較",   "pages/3_股票比較"),
        ("health",  "✦", "資料健康",   "pages/4_資料健康"),
    ]
    with st.sidebar:
        st.markdown(
            """
            <div class="sl-logo">
                <div class="sl-logo-mark">SL</div>
                <div>
                    <div class="sl-logo-text">StockLens</div>
                    <div class="sl-logo-sub">台股量化分析</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for key, icon, label, _ in pages:
            cls = "nav-item active" if key == active else "nav-item"
            st.markdown(
                f'<div class="{cls}"><span class="nav-icon">{icon}</span>{label}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            """
            <div class="sidebar-footer">
                資料來源：FinMind<br>
                資料期間：近 365 天<br>
                追蹤股票：30 檔<br><br>
                ⚠️ 僅供研究參考，不構成投資建議
            </div>
            """,
            unsafe_allow_html=True,
        )


def page_header(title: str, subtitle: str = "", updated: str = ""):
    upd = f'<div class="page-updated">最後更新：{updated}</div>' if updated else ""
    st.markdown(
        f"""
        <div class="page-header">
            <div>
                <div class="page-title">{title}</div>
                {"" if not subtitle else f'<div class="page-sub">{subtitle}</div>'}
            </div>
            {upd}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(icon, label, value, sub="", tone="blue", badge=None):
    bdg = f'<span class="pill">{badge}</span>' if badge else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-icon {tone}">{icon}</div>'
        f'<div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {tone}">{value}{bdg}</div>'
        f'{"" if not sub else f"<div class=kpi-sub>{sub}</div>"}'
        f'</div></div>'
    )


def card_open(title: str, info: bool = False):
    info_html = '<span class="info-dot">i</span>' if info else ""
    st.markdown(
        f'<div class="card"><div class="card-title">{title} {info_html}</div>',
        unsafe_allow_html=True,
    )


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def ranking_html(df, metric_col, metric_label, ascending=False, use_abs_bar=False):
    ranked = (
        df.dropna(subset=[metric_col])
        .sort_values(metric_col, ascending=ascending)
        .head(10).copy()
    )
    if ranked.empty:
        return '<div style="padding:1rem;color:#64748b;">目前無資料。</div>'

    bar_vals = ranked[metric_col].abs() if use_abs_bar else ranked[metric_col]
    max_val  = max(float(bar_vals.max()), 0.0001)

    def rows(part, offset):
        out = []
        for i, row in enumerate(part.itertuples(index=False), start=offset):
            val = getattr(row, metric_col)
            bv  = abs(val) if use_abs_bar else val
            w   = max(5, min(100, bv/max_val*100)) if pd.notna(val) else 0
            cls = metric_class(val, positive_is_good=(metric_col != "volatility_20d"))
            if metric_col == "volume_ratio":   display, cls = ratio(val),  "orange-text"
            elif metric_col == "health_score": display, cls = number(val,1),"positive"
            else:                              display = pct(val)
            out.append(
                f'<tr><td class="num">{i}</td><td>{row.stock_id}</td><td>{row.name}</td>'
                f'<td><div class="bar-bg"><div class="bar-fill" style="width:{w:.0f}%"></div></div></td>'
                f'<td class="{cls}" style="text-align:right">{display}</td></tr>'
            )
        return "\n".join(out)

    hdr = (
        '<tr><th style="width:40px">排名</th><th style="width:80px">代號</th>'
        f'<th>名稱</th><th style="width:140px"></th>'
        f'<th style="text-align:right">{metric_label}</th></tr>'
    )
    left, right = ranked.iloc[:5], ranked.iloc[5:]
    return (
        '<div class="rank-grid">'
        f'<table class="rank-table">{hdr}{rows(left,1)}</table>'
        f'<table class="rank-table right">{hdr}{rows(right,6)}</table>'
        '</div>'
    )


def render_ranking(df, metric_col, metric_label, ascending=False, use_abs_bar=False, height=310):
    components.html(RANKING_CSS + ranking_html(df, metric_col, metric_label, ascending, use_abs_bar),
                    height=height, scrolling=False)