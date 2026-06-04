"""pages/4_資料健康.py — 資料品質視覺化"""

import altair as alt
import pandas as pd
import streamlit as st

from utils.db import read_quality_check, read_stocks
from utils.formatters import category_label, CATEGORY_LABELS
from utils.style import inject_css, render_sidebar, page_header, card_open, card_close, kpi_card
from utils.charts import _AXIS

st.set_page_config(page_title="StockLens | 資料健康", page_icon="✦", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
render_sidebar("health")

try:
    qdf    = read_quality_check()
    stocks = read_stocks()
except Exception as e:
    st.error("無法讀取資料庫。"); st.code(str(e)); st.stop()

page_header("資料健康", "daily_prices 資料品質檢查與覆蓋率分析")

if qdf.empty:
    st.warning("目前沒有資料，請先執行 ETL。"); st.stop()

qdf["rows"]            = pd.to_numeric(qdf["rows"],            errors="coerce").fillna(0).astype(int)
qdf["missing_close"]   = pd.to_numeric(qdf["missing_close"],   errors="coerce").fillna(0).astype(int)
qdf["missing_volume"]  = pd.to_numeric(qdf["missing_volume"],  errors="coerce").fillna(0).astype(int)
qdf["abnormal_price"]  = pd.to_numeric(qdf["abnormal_price"],  errors="coerce").fillna(0).astype(int)
qdf["abnormal_volume"] = pd.to_numeric(qdf["abnormal_volume"],  errors="coerce").fillna(0).astype(int)
qdf["category_tw"]     = qdf["category"].apply(category_label)

total_rows   = int(qdf["rows"].sum())
total_stocks = len(qdf)
miss_close   = int(qdf["missing_close"].sum())
miss_vol     = int(qdf["missing_volume"].sum())
abn_price    = int(qdf["abnormal_price"].sum())
abn_vol      = int(qdf["abnormal_volume"].sum())

# ── KPI ──────────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5,k6 = st.columns(6, gap="medium")
for col, lbl, val, tone in [
    (k1, "追蹤股票數",    f"{total_stocks} 檔", "blue"),
    (k2, "總資料筆數",    f"{total_rows:,}",     "blue"),
    (k3, "close 空值",    str(miss_close),       "green" if miss_close==0 else "orange"),
    (k4, "volume 空值",   str(miss_vol),         "green" if miss_vol==0   else "orange"),
    (k5, "價格異常",      str(abn_price),        "green" if abn_price==0  else "orange"),
    (k6, "成交量異常",    str(abn_vol),          "green" if abn_vol==0    else "orange"),
]:
    with col:
        icon = "✓" if val in ["0","0 檔"] or (tone == "green") else "!"
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-icon {tone}">{icon}</div>'
            f'<div><div class="kpi-label">{lbl}</div>'
            f'<div class="kpi-value {tone}">{val}</div></div></div>',
            unsafe_allow_html=True)

# ── 狀態 badge ────────────────────────────────────────────────────────────────
total_issues = miss_close + miss_vol + abn_price + abn_vol
if total_issues == 0:
    st.markdown(
        '<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-left:4px solid #149b55;'
        'border-radius:8px;padding:.65rem 1rem;color:#166534;font-size:.88rem;margin:.6rem 0;">'
        '✅ 資料品質良好，目前沒有發現任何異常或空值。</div>',
        unsafe_allow_html=True)
else:
    st.markdown(
        f'<div style="background:#fefce8;border:1px solid #fde68a;border-left:4px solid #f59e0b;'
        f'border-radius:8px;padding:.65rem 1rem;color:#78350f;font-size:.88rem;margin:.6rem 0;">'
        f'⚠️ 共發現 {total_issues} 筆異常或空值，請檢查下方明細。</div>',
        unsafe_allow_html=True)

st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)

# ── 每檔股票資料筆數 ──────────────────────────────────────────────────────────
card_open("每檔股票資料筆數")
bar_df = qdf.sort_values("rows", ascending=False).copy()
bar_df["label"] = bar_df["stock_id"] + " " + bar_df["name"]
avg_rows = bar_df["rows"].mean()

bars = (
    alt.Chart(bar_df)
    .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
    .encode(
        x=alt.X("rows:Q", title="資料筆數"),
        y=alt.Y("label:N", sort="-x", title=None),
        color=alt.Color("category_tw:N", legend=alt.Legend(title="產業", orient="right")),
        tooltip=[
            alt.Tooltip("label:N",      title="股票"),
            alt.Tooltip("rows:Q",       title="資料筆數"),
            alt.Tooltip("start_date:T", title="起始日", format="%Y-%m-%d"),
            alt.Tooltip("end_date:T",   title="結束日", format="%Y-%m-%d"),
            alt.Tooltip("category_tw:N",title="產業"),
        ],
    ).properties(height=580, background="#ffffff")
)
avg_line = (
    alt.Chart(pd.DataFrame({"x":[avg_rows]}))
    .mark_rule(color="#0f6fe8", strokeDash=[5,4], strokeWidth=1.5)
    .encode(x="x:Q")
)
st.altair_chart(
    alt.layer(bars, avg_line)
    .configure_axis(**_AXIS).configure_view(stroke=None),
    use_container_width=True, theme=None)
card_close()

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 產業覆蓋率 ────────────────────────────────────────────────────────────────
left, right = st.columns([1, 1.4], gap="medium")

with left:
    card_open("產業資料覆蓋率")
    cat_df = (
        qdf.groupby("category_tw")
        .agg(股票數=("stock_id","count"), 總筆數=("rows","sum"),
             平均筆數=("rows","mean"))
        .reset_index()
        .rename(columns={"category_tw":"產業"})
    )
    cat_df["平均筆數"] = cat_df["平均筆數"].round(0).astype(int)
    st.dataframe(cat_df, use_container_width=True, hide_index=True)
    card_close()

with right:
    card_open("異常 / 空值明細")
    issue_df = qdf[
        (qdf["missing_close"]>0)|(qdf["missing_volume"]>0)|
        (qdf["abnormal_price"]>0)|(qdf["abnormal_volume"]>0)
    ][["stock_id","name","category_tw","missing_close",
       "missing_volume","abnormal_price","abnormal_volume"]].copy()
    issue_df.columns = ["代號","名稱","產業","close空值","volume空值","價格異常","量異常"]
    if issue_df.empty:
        st.success("✅ 無任何異常記錄")
    else:
        st.dataframe(issue_df, use_container_width=True, hide_index=True)
    card_close()

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 完整品質表 ────────────────────────────────────────────────────────────────
with st.expander("📋 完整資料品質表"):
    full_df = qdf[["stock_id","name","category_tw","rows",
                   "start_date","end_date","missing_close",
                   "missing_volume","abnormal_price","abnormal_volume"]].copy()
    full_df.columns = ["代號","名稱","產業","資料筆數","起始日","結束日",
                       "close空值","volume空值","價格異常","量異常"]
    st.dataframe(full_df, use_container_width=True, hide_index=True)