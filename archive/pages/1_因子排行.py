"""pages/1_因子排行.py — 完整因子排行與篩選"""

import altair as alt
import pandas as pd
import streamlit as st

from utils.db import read_latest_factors
from utils.formatters import pct, number, ratio, category_label, CATEGORY_LABELS, metric_class
from utils.style import inject_css, render_sidebar, page_header, card_open, card_close, render_ranking
from utils.charts import _AXIS

st.set_page_config(page_title="StockLens | 因子排行", page_icon="≡", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
render_sidebar("ranking")

try:
    factors = read_latest_factors()
except Exception as e:
    st.error("無法讀取資料庫。"); st.code(str(e)); st.stop()

latest_dt = pd.to_datetime(factors["date"]).max().strftime("%Y-%m-%d")
page_header("因子排行", "30 檔股票完整排行，可切換指標與篩選產業", latest_dt)

# ── 篩選列 ────────────────────────────────────────────────────────────────────
METRICS = {
    "20日報酬率": ("return_20d",    "20日報酬率", False, False),
    "60日報酬率": ("return_60d",    "60日報酬率", False, False),
    "健康分數":   ("health_score",  "健康分數",   False, False),
    "波動率":     ("volatility_20d","波動率",     True,  True),
    "最大回撤":   ("max_drawdown",  "最大回撤",   True,  True),
    "成交量倍率": ("volume_ratio",  "成交量倍率", False, False),
}

f1, f2 = st.columns([1.2, 2], gap="medium")
with f1:
    metric_label = st.selectbox("排序指標", list(METRICS.keys()), label_visibility="visible")
with f2:
    cat_opts = ["全部"] + [CATEGORY_LABELS[k] for k in CATEGORY_LABELS]
    cats = st.multiselect("篩選產業", cat_opts, default=["全部"], label_visibility="visible")

mc, ml, asc, abs_bar = METRICS[metric_label]

# 過濾
df = factors.copy()
df["category_tw"] = df["category"].apply(category_label)
if cats and "全部" not in cats:
    df = df[df["category_tw"].isin(cats)]

if df.empty:
    st.info("目前選擇的條件沒有資料。"); st.stop()

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 上半：Top 10 排行 + 右側 Bar chart ────────────────────────────────────────
left, right = st.columns([1.6, 1], gap="medium")

with left:
    card_open(f"Top 10 — {metric_label}")
    render_ranking(df, mc, ml, asc, abs_bar, height=330)
    card_close()

with right:
    card_open(f"Top 10 Bar Chart")
    top10 = (
        df.dropna(subset=[mc])
        .sort_values(mc, ascending=asc)
        .head(10).copy()
    )
    top10["label"]    = top10["stock_id"] + " " + top10["name"]
    top10["display"]  = top10[mc] * (100 if mc not in ["health_score","volume_ratio"] else 1)
    top10["顏色"] = top10[mc].apply(
        lambda v: "#149b55" if (v >= 0 if not asc else v <= 0) else "#ef4444"
    )
    if mc == "health_score":
        top10["顏色"] = top10[mc].apply(
            lambda v: "#149b55" if v >= 65 else ("#f59e0b" if v >= 50 else "#ef4444"))
    if mc == "volume_ratio":
        top10["顏色"] = "#f59e0b"

    fmt = ".1f" if mc in ["health_score","volume_ratio"] else "+.1f"
    bar = (
        alt.Chart(top10)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("display:Q", title=ml, axis=alt.Axis(format=fmt)),
            y=alt.Y("label:N", sort=None, title=None),
            color=alt.Color("顏色:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("label:N",   title="股票"),
                alt.Tooltip("display:Q", title=ml, format=fmt),
            ],
        )
        .properties(height=310, background="#ffffff")
        .configure_axis(**_AXIS)
        .configure_view(stroke=None)
    )
    st.altair_chart(bar, use_container_width=True, theme=None)
    card_close()

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 下半：完整排行表 ──────────────────────────────────────────────────────────
card_open("完整排行（可排序）")

sorted_df = (
    df.dropna(subset=[mc])
    .sort_values(mc, ascending=asc)
    .reset_index(drop=True)
    .copy()
)
sorted_df.index += 1

def fmt_val(v, col):
    if col in ["return_20d","return_60d","volatility_20d","max_drawdown"]:
        return pct(v)
    if col == "health_score":   return number(v,1)
    if col == "volume_ratio":   return ratio(v)
    return str(v)

display_df = sorted_df[["stock_id","name","category","return_20d","return_60d",
                          "volatility_20d","max_drawdown","volume_ratio","health_score"]].copy()
display_df.columns = ["代號","名稱","產業","20日報酬","60日報酬","波動率","最大回撤","量倍率","健康分數"]
display_df["產業"]   = display_df["產業"].apply(category_label)
display_df["20日報酬"] = sorted_df["return_20d"].apply(pct)
display_df["60日報酬"] = sorted_df["return_60d"].apply(pct)
display_df["波動率"]   = sorted_df["volatility_20d"].apply(pct)
display_df["最大回撤"] = sorted_df["max_drawdown"].apply(pct)
display_df["量倍率"]   = sorted_df["volume_ratio"].apply(ratio)
display_df["健康分數"] = sorted_df["health_score"].apply(lambda v: number(v,1))

st.dataframe(display_df, use_container_width=True, height=480)
card_close()

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ── 報酬 vs 風險散點圖 ──────────────────────────────────────────────────────
card_open("報酬 vs 風險分布")

scatter_df = df.dropna(subset=["return_20d","volatility_20d"]).copy()
scatter_df["報酬率(%)"] = scatter_df["return_20d"]    * 100
scatter_df["波動率(%)"] = scatter_df["volatility_20d"] * 100
scatter_df["label"]     = scatter_df["stock_id"] + " " + scatter_df["name"]
scatter_df["category_tw"] = scatter_df["category"].apply(category_label)

scatter = (
    alt.Chart(scatter_df)
    .mark_circle(size=80, opacity=.85, stroke="white", strokeWidth=1.2)
    .encode(
        x=alt.X("報酬率(%):Q", title="20日報酬率 (%)", scale=alt.Scale(zero=False)),
        y=alt.Y("波動率(%):Q", title="20日波動率 (%)", scale=alt.Scale(zero=False)),
        color=alt.Color("category_tw:N",
            legend=alt.Legend(title="產業", orient="right")),
        tooltip=[
            alt.Tooltip("label:N",      title="股票"),
            alt.Tooltip("報酬率(%):Q",  title="20日報酬率",  format=".2f"),
            alt.Tooltip("波動率(%):Q",  title="20日波動率",  format=".2f"),
            alt.Tooltip("health_score:Q",title="健康分數",   format=".1f"),
        ],
    )
    .properties(height=340, background="#ffffff")
    .configure_axis(**_AXIS)
    .configure_view(stroke=None)
)
st.altair_chart(scatter, use_container_width=True, theme=None)
card_close()