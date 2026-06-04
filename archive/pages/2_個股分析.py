"""pages/2_個股分析.py — 深入個股研究"""

import pandas as pd
import streamlit as st

from utils.db import read_latest_factors, read_stocks, read_stock_prices
from utils.formatters import (pct, pct_plain, number, ratio,
                               category_label, health_label, metric_class, cluster_tag)
from utils.charts import render_price_chart, render_volume_chart
from utils.style import inject_css, render_sidebar, page_header, card_open, card_close
from utils.pdf_report import generate_pdf

st.set_page_config(page_title="StockLens | 個股分析", page_icon="◎", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
render_sidebar("stock")

try:
    factors = read_latest_factors()
    stocks  = read_stocks()
except Exception as e:
    st.error("無法讀取資料庫。"); st.code(str(e)); st.stop()

cluster_map = cluster_tag(factors)
latest_dt   = pd.to_datetime(factors["date"]).max().strftime("%Y-%m-%d")
page_header("個股分析", "深入研究單一股票的走勢與量化因子", latest_dt)

# ── 選股 ─────────────────────────────────────────────────────────────────────
opts    = [f"{r.stock_id}　{r.name}" for r in stocks.itertuples(index=False)]
def_idx = next((i for i,o in enumerate(opts) if o.startswith("2330")), 0)
sel     = st.selectbox("選擇股票", opts, index=def_idx, label_visibility="collapsed")
sid     = sel.split("　",1)[0]
sr      = stocks.loc[stocks["stock_id"]==sid].iloc[0].to_dict()
fm      = factors.loc[factors["stock_id"]==sid]
fr      = fm.iloc[0] if not fm.empty else pd.Series(dtype="object")
prices  = read_stock_prices(sid)

lc  = prices["close"].iloc[-1] if not prices.empty else fr.get("latest_close", float("nan"))
lpd = prices["date"].max().date() if not prices.empty else pd.to_datetime(factors["date"]).max().date()
r20 = fr.get("return_20d",    float("nan"))
r60 = fr.get("return_60d",    float("nan"))
vol = fr.get("volatility_20d",float("nan"))
dd  = fr.get("max_drawdown",  float("nan"))
vr  = fr.get("volume_ratio",  float("nan"))
sc  = fr.get("health_score",  float("nan"))
cl  = fr.get("cluster_label", float("nan"))

cl_text  = cluster_map.get(int(cl), f"Cluster {int(cl)}") if pd.notna(cl) else "-"
cl_color = {"強勢":"#149b55","穩健":"#0f6fe8","弱勢":"#ef4444"}.get(cl_text,"#64748b")

st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)

# ── 基本資料列 ────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5, gap="medium")
for col, lbl, val, tone in [
    (c1, "股票代號",  sid,               "blue"),
    (c2, "股票名稱",  sr["name"],        "blue"),
    (c3, "產業分類",  category_label(sr["category"]), "blue"),
    (c4, "最新收盤",  number(lc,2),      "green"),
    (c5, "資料日期",  str(lpd),          "blue"),
]:
    with col:
        st.markdown(
            f'<div class="kpi-card"><div>'
            f'<div class="kpi-label">{lbl}</div>'
            f'<div class="kpi-value {tone}" style="font-size:1.15rem">{val}</div>'
            f'</div></div>',
            unsafe_allow_html=True)

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 指標卡片列 ────────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5, m6 = st.columns(6, gap="medium")
metrics = [
    (m1, "20日報酬率", pct(r20),       metric_class(r20)),
    (m2, "60日報酬率", pct(r60),       metric_class(r60)),
    (m3, "波動率",     pct_plain(vol), "blue-text"),
    (m4, "最大回撤",   pct(dd),        "negative"),
    (m5, "成交量倍率", ratio(vr),      "orange-text"),
    (m6, "健康分數",   f"{number(sc,1)}/100", "positive"),
]
for col, lbl, val, cls in metrics:
    with col:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">{lbl}</div>'
            f'<div class="metric-value {cls}">{val}</div>'
            f'</div>',
            unsafe_allow_html=True)

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 走勢圖 ────────────────────────────────────────────────────────────────────
card_open("收盤價走勢 ＋ 成交量")

RANGE_MAP = {"1M": 21, "3M": 63, "6M": 126, "1Y": 252}
rng = st.radio("時間區間", list(RANGE_MAP.keys()), index=2, horizontal=True,
               label_visibility="collapsed")
days = RANGE_MAP[rng]
render_price_chart(prices, days=days)
render_volume_chart(prices, days=days)
card_close()

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 分群解釋 + 下載 ───────────────────────────────────────────────────────────
left, right = st.columns([1.6, 1], gap="medium")

with left:
    card_open("K-means 分群解釋")
    cluster_desc = {
        "強勢": "此股票目前歸屬於「強勢」群組，代表近期報酬率較高、健康分數較佳，相對其他追蹤股票表現領先。",
        "穩健": "此股票目前歸屬於「穩健」群組，代表各項因子表現中等，風險與報酬均衡。",
        "弱勢": "此股票目前歸屬於「弱勢」群組，代表近期報酬率偏低或波動風險較高，需留意。",
        "-":    "目前尚無 K-means 分群結果，請先執行 stock_factors.py --cluster。",
    }
    st.markdown(
        f"""
        <div class="card" style="margin-top:0">
            <div style="display:flex;align-items:center;gap:.7rem;margin-bottom:.6rem;">
                <div style="font-size:1.6rem;font-weight:900;color:{cl_color};">{cl_text}</div>
                <div style="color:#64748b;font-size:.85rem;">K-means 分群結果</div>
            </div>
            <div style="color:#334155;font-size:.9rem;line-height:1.8;">
                {cluster_desc.get(cl_text, cluster_desc["-"])}
            </div>
            <div style="margin-top:.8rem;color:#94a3b8;font-size:.78rem;">
                健康狀態評級：<strong style="color:#0b1f3f">{health_label(sc)}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True)
    card_close()

with right:
    card_open("下載分析報告")
    st.markdown(
        '<div style="color:#5d6d86;font-size:.85rem;margin-bottom:.8rem;line-height:1.7;">'
        f'股票：<strong>{sid} {sr["name"]}</strong><br>'
        f'日期：{lpd}<br>'
        '格式：PDF'
        '</div>',
        unsafe_allow_html=True)

    try:
        pdf_bytes = generate_pdf(
            stock_id=sid, name=sr["name"],
            category=category_label(sr["category"]),
            market=sr.get("market","TSE"),
            latest_date=lpd, latest_close=lc,
            r20=r20, r60=r60, vol=vol, drawdown=dd,
            vol_ratio=vr, score=sc,
            cluster_text=cl_text,
            health_lbl=health_label(sc),
        )
        st.download_button(
            "⬇ 下載 PDF 報告",
            data=pdf_bytes,
            file_name=f"stocklens_{sid}_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.warning(f"PDF 產生失敗：{e}")

    card_close()