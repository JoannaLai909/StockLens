"""app.py — StockLens 首頁：市場總覽"""

import pandas as pd
import streamlit as st

from utils.db import read_latest_factors, read_industry_avg, read_stocks, read_stock_prices
from utils.formatters import pct, pct_plain, number, ratio, category_label, health_label, metric_class, cluster_tag
from utils.charts import render_health_scatter, render_industry_chart, render_price_chart
from utils.style import inject_css, render_sidebar, page_header, kpi_card, card_open, card_close, render_ranking

st.set_page_config(page_title="StockLens | 市場總覽", page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
render_sidebar("home")

# ── 資料 ─────────────────────────────────────────────────────────────────────
try:
    factors  = read_latest_factors()
    industry = read_industry_avg()
    stocks   = read_stocks()
except Exception as e:
    st.error("無法讀取資料庫。請確認 Docker Compose 已啟動。")
    st.code(str(e)); st.stop()

if factors.empty:
    st.warning("目前沒有 factor_scores 資料。請先執行 ETL 與 stock_factors.py。")
    st.stop()

cluster_map   = cluster_tag(factors)
latest_dt     = pd.to_datetime(factors["date"]).max().strftime("%Y-%m-%d")
avg_health    = factors["health_score"].mean()
best          = factors.dropna(subset=["return_20d"]).sort_values("return_20d", ascending=False).head(1)
best_row      = best.iloc[0] if not best.empty else None

# ── 頁首 ─────────────────────────────────────────────────────────────────────
page_header("StockLens 台股量化分析平台",
            "整合股價資料、量化因子與互動式圖表，快速掌握股票表現與風險",
            f"{latest_dt} 15:30")

# ── KPI ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    st.markdown(kpi_card("◎","追蹤股票數",f"{len(factors)}","檔股票","blue"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("□","最新資料日期",latest_dt,"每日更新","blue"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("♡","平均健康分數",number(avg_health,1),"/ 100","green"), unsafe_allow_html=True)
with k4:
    if best_row is not None:
        st.markdown(kpi_card("↗","20日報酬最佳",str(best_row["stock_id"]),
                             str(best_row["name"]),"green",pct(best_row["return_20d"],1)),
                    unsafe_allow_html=True)
    else:
        st.markdown(kpi_card("↗","20日報酬最佳","-","-","green"), unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ── 圖表雙欄 ─────────────────────────────────────────────────────────────────
c1, c2 = st.columns([1.05, 1.3], gap="medium")
with c1:
    card_open("市場健康分布", info=True)
    render_health_scatter(factors)
    card_close()
with c2:
    card_open("產業平均健康分數", info=True)
    render_industry_chart(industry)
    card_close()

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ── 排行 Top 10 ───────────────────────────────────────────────────────────────
card_open("因子排行 Top 10")

TABS = {
    "20日報酬": ("return_20d",    "20日報酬率", False, False),
    "60日報酬": ("return_60d",    "60日報酬率", False, False),
    "健康分數": ("health_score",  "健康分數",   False, False),
    "波動率":   ("volatility_20d","波動率",     False, True),
    "最大回撤": ("max_drawdown",  "最大回撤",   True,  True),
}
tab = st.radio("指標", list(TABS), horizontal=True, label_visibility="collapsed")
mc, ml, asc, abs_bar = TABS[tab]
render_ranking(factors, mc, ml, asc, abs_bar)
card_close()

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ── 個股快速分析 ──────────────────────────────────────────────────────────────
card_open("個股快速分析")

opts = [f"{r.stock_id}　{r.name}" for r in stocks.itertuples(index=False)]
def_idx = next((i for i,o in enumerate(opts) if o.startswith("2330")), 0)
sel = st.selectbox("選擇股票", opts, index=def_idx, label_visibility="collapsed")
sid = sel.split("　",1)[0]
stock_row   = stocks.loc[stocks["stock_id"]==sid].iloc[0].to_dict()
factor_match= factors.loc[factors["stock_id"]==sid]
fr          = factor_match.iloc[0] if not factor_match.empty else pd.Series(dtype="object")
prices      = read_stock_prices(sid)

lc   = prices["close"].iloc[-1] if not prices.empty else fr.get("latest_close", float("nan"))
lpd  = prices["date"].max().date() if not prices.empty else pd.to_datetime(factors["date"]).max().date()
r20  = fr.get("return_20d",    float("nan"))
r60  = fr.get("return_60d",    float("nan"))
vol  = fr.get("volatility_20d",float("nan"))
dd   = fr.get("max_drawdown",  float("nan"))
vr   = fr.get("volume_ratio",  float("nan"))
sc   = fr.get("health_score",  float("nan"))
cl   = fr.get("cluster_label", float("nan"))

if pd.notna(cl):
    cl_text  = cluster_map.get(int(cl), f"Cluster {int(cl)}")
    cl_color = {"強勢":"#149b55","穩健":"#0f6fe8","弱勢":"#ef4444"}.get(cl_text,"#0f6fe8")
else:
    cl_text, cl_color = "-", "#64748b"

ql, qm, qr = st.columns([1, 1.8, 2.6], gap="medium")

with ql:
    st.markdown(
        f"""
        <div class="stock-info-card">
            <div class="stock-id-badge">{sid}</div>
            <div class="stock-name">{stock_row["name"]}</div>
            <div class="stock-meta">
                產業：{category_label(stock_row["category"])}<br>
                市場：{stock_row.get("market","TSE")}<br>
                資料日：{lpd}<br>
                收盤：<strong>{number(lc,2)}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

with qm:
    st.markdown(
        """<div style="font-weight:800;color:#10284a;font-size:.9rem;margin-bottom:.3rem;">
           收盤價走勢（近 6 個月）</div>""",
        unsafe_allow_html=True)
    render_price_chart(prices)

with qr:
    st.markdown(
        f"""
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:.55rem;margin-bottom:.55rem;">
            <div class="metric-card"><div class="metric-label">20日報酬率</div>
                <div class="metric-value {metric_class(r20)}">{pct(r20)}</div></div>
            <div class="metric-card"><div class="metric-label">60日報酬率</div>
                <div class="metric-value {metric_class(r60)}">{pct(r60)}</div></div>
            <div class="metric-card"><div class="metric-label">波動率</div>
                <div class="metric-value blue-text">{pct_plain(vol)}</div></div>
            <div class="metric-card"><div class="metric-label">最大回撤</div>
                <div class="metric-value negative">{pct(dd)}</div></div>
            <div class="metric-card"><div class="metric-label">成交量倍率</div>
                <div class="metric-value orange-text">{ratio(vr)}</div></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:.55rem;">
            <div class="score-card">
                <div class="metric-label">健康分數</div>
                <div class="metric-value positive">{number(sc,1)}<span style="font-size:.8rem;color:#64748b;"> / 100</span></div>
            </div>
            <div class="cluster-card">
                <div class="metric-label">K-means 分群</div>
                <div class="metric-value" style="color:{cl_color};">{cl_text}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

card_close()