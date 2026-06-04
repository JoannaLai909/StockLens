"""pages/3_股票比較.py — 多股票比較，統一新版風格"""

import altair as alt
import pandas as pd
import streamlit as st

from utils.db import read_latest_factors, read_stocks, read_prices_multi
from utils.formatters import category_label, number
from utils.style import inject_css, render_sidebar, page_header, card_open, card_close
from utils.charts import _AXIS

st.set_page_config(page_title="StockLens | 股票比較", page_icon="⇌", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
render_sidebar("compare")

try:
    factors = read_latest_factors()
    stocks  = read_stocks()
except Exception as e:
    st.error("無法讀取資料庫。"); st.code(str(e)); st.stop()

latest_dt = pd.to_datetime(factors["date"]).max().strftime("%Y-%m-%d")
page_header("股票比較", "選擇 2–5 檔股票，比較報酬、風險與量能", latest_dt)

PALETTE = ["#0f6fe8","#149b55","#f59e0b","#ef4444","#8b5cf6"]

# ── 選股 ─────────────────────────────────────────────────────────────────────
opts    = [f"{r.stock_id}　{r.name}" for r in stocks.itertuples(index=False)]
opt_map = {f"{r.stock_id}　{r.name}": r.stock_id for r in stocks.itertuples(index=False)}

sel_labels = st.multiselect("選擇 2–5 檔股票進行比較", opts,
                             max_selections=5, placeholder="請選擇股票…")
if len(sel_labels) < 2:
    st.markdown(
        '<div style="background:#f0f9ff;border:1px solid #bae6fd;border-left:4px solid #0f6fe8;'
        'border-radius:8px;padding:.7rem 1rem;color:#0c4a6e;font-size:.88rem;margin-top:.5rem;">'
        '👆 請至少選擇 <strong>2 檔</strong>股票，最多可選 5 檔。</div>',
        unsafe_allow_html=True)
    st.stop()

sel_ids  = [opt_map[lb] for lb in sel_labels]
comp_df  = factors[factors["stock_id"].isin(sel_ids)].copy()
comp_df["label"] = comp_df["stock_id"] + "　" + comp_df["name"]
color_map = {sid: PALETTE[i] for i,sid in enumerate(sel_ids)}
comp_df["color"] = comp_df["stock_id"].map(color_map)

labels_ord = [comp_df[comp_df["stock_id"]==sid]["label"].values[0]
               for sid in sel_ids if sid in comp_df["stock_id"].values]
c_scale = alt.Scale(domain=labels_ord,
                    range=[color_map[s] for s in sel_ids if s in comp_df["stock_id"].values])

st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)

# ── 個股摘要卡 ────────────────────────────────────────────────────────────────
card_open("個股摘要")
cols = st.columns(len(sel_ids), gap="medium")
for col, sid in zip(cols, sel_ids):
    rows = comp_df[comp_df["stock_id"]==sid]
    if rows.empty: col.warning(f"{sid} 無資料"); continue
    row = rows.iloc[0]
    sc  = float(row["health_score"]) if pd.notna(row["health_score"]) else 0
    sc_color = "#149b55" if sc>=65 else ("#f59e0b" if sc>=45 else "#ef4444")
    accent = color_map[sid]
    with col:
        st.markdown(
            f"""
            <div class="card" style="border-top:4px solid {accent};padding:.9rem 1rem;">
                <div style="font-size:.72rem;font-weight:800;color:#64748b;text-transform:uppercase;
                            letter-spacing:.05em;">{row["stock_id"]} · {category_label(row["category"])}</div>
                <div style="font-size:1rem;font-weight:800;color:#0b1f3f;margin:.2rem 0;">{row["name"]}</div>
                <div style="font-size:1.4rem;font-weight:900;color:#0b1f3f;">{row["latest_close"]:.2f}</div>
                <div style="font-size:.75rem;color:#94a3b8;margin-top:.15rem;">
                    因子日期：{pd.to_datetime(row["date"]).date()}</div>
                <div style="font-size:.72rem;color:#64748b;margin-top:.5rem;">Health Score</div>
                <div style="font-size:1.15rem;font-weight:800;color:{sc_color};">{number(row["health_score"],1)}</div>
            </div>
            """, unsafe_allow_html=True)
card_close()

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 報酬率比較 ────────────────────────────────────────────────────────────────
card_open("報酬率比較")
ret_long = (
    comp_df[["label","return_20d","return_60d"]]
    .melt(id_vars="label", value_vars=["return_20d","return_60d"],
          var_name="period", value_name="ret")
)
ret_long["ret_pct"] = ret_long["ret"] * 100
ret_long["period"]  = ret_long["period"].map({"return_20d":"20日報酬率","return_60d":"60日報酬率"})

bar = (
    alt.Chart(ret_long)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        x=alt.X("period:N", title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("label:N", sort=labels_ord),
        y=alt.Y("ret_pct:Q", title="報酬率 (%)", axis=alt.Axis(format=".1f")),
        color=alt.Color("label:N", scale=c_scale, legend=alt.Legend(title="股票", orient="top")),
        tooltip=[
            alt.Tooltip("label:N",   title="股票"),
            alt.Tooltip("period:N",  title="期間"),
            alt.Tooltip("ret_pct:Q", title="報酬率 (%)", format=".2f"),
        ],
    ).properties(height=280)
)
zero = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(color="#94a3b8",strokeWidth=1).encode(y="y:Q")
st.altair_chart(
    alt.layer(bar,zero).configure_axis(**_AXIS).configure_view(stroke=None),
    use_container_width=True, theme=None)
card_close()

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 風險指標 ──────────────────────────────────────────────────────────────────
r1, r2 = st.columns(2, gap="medium")

def horiz_bar(df, x_col, x_title, title, fmt=".2f", ref_x=None):
    chart_df = df.copy()
    b = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X(f"{x_col}:Q", title=x_title, axis=alt.Axis(format=fmt)),
            y=alt.Y("label:N", sort=labels_ord, title=None),
            color=alt.Color("label:N", scale=c_scale, legend=None),
            tooltip=[alt.Tooltip("label:N",title="股票"),
                     alt.Tooltip(f"{x_col}:Q",title=x_title,format=fmt)],
        ).properties(height=220, title=title)
    )
    if ref_x is not None:
        ref = (alt.Chart(pd.DataFrame({"x":[ref_x]}))
               .mark_rule(color="#94a3b8",strokeDash=[4,3],strokeWidth=1.2)
               .encode(x="x:Q"))
        b = alt.layer(b, ref)
    return b.configure_axis(**_AXIS).configure_view(stroke=None)

with r1:
    card_open("波動率比較")
    vol_df = comp_df.copy(); vol_df["vol_pct"] = vol_df["volatility_20d"] * 100
    st.altair_chart(horiz_bar(vol_df,"vol_pct","波動率 (%)","波動率（越低越穩定）"),
                    use_container_width=True, theme=None)
    card_close()

with r2:
    card_open("最大回撤比較")
    dd_df = comp_df.copy(); dd_df["dd_pct"] = dd_df["max_drawdown"].abs() * 100
    st.altair_chart(horiz_bar(dd_df,"dd_pct","最大回撤 (%)","最大回撤（越低跌幅越小）"),
                    use_container_width=True, theme=None)
    card_close()

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 量能 & 健康分數 ───────────────────────────────────────────────────────────
q1, q2 = st.columns(2, gap="medium")

with q1:
    card_open("成交量倍率")
    st.altair_chart(horiz_bar(comp_df,"volume_ratio","成交量倍率",
                              "成交量倍率（>1 代表近期量能放大）",fmt=".2f",ref_x=1),
                    use_container_width=True, theme=None)
    card_close()

with q2:
    card_open("綜合健康分數")
    hs = (
        alt.Chart(comp_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("health_score:Q", title="Health Score", scale=alt.Scale(domain=[0,100])),
            y=alt.Y("label:N", sort=labels_ord, title=None),
            color=alt.Color("health_score:Q",
                scale=alt.Scale(domain=[0,50,100],range=["#ef4444","#f59e0b","#149b55"]),
                legend=None),
            tooltip=[alt.Tooltip("label:N",title="股票"),
                     alt.Tooltip("health_score:Q",title="Health Score",format=".1f")],
        ).properties(height=220, title="綜合健康分數（0–100，越高越好）")
    )
    st.altair_chart(hs.configure_axis(**_AXIS).configure_view(stroke=None),
                    use_container_width=True, theme=None)
    card_close()

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

# ── 收盤價標準化走勢 ──────────────────────────────────────────────────────────
card_open("收盤價走勢比較（標準化至 100）")
st.markdown(
    '<div style="font-size:.82rem;color:#64748b;margin-bottom:.5rem;">'
    '以各股最早共同交易日為基準設為 100，消除絕對價格差異，方便直接比較漲跌幅。</div>',
    unsafe_allow_html=True)

try:
    prices = read_prices_multi(tuple(sel_ids))
except Exception as e:
    st.warning(f"無法載入股價資料：{e}"); prices = pd.DataFrame()

if not prices.empty:
    first_dates  = prices.groupby("stock_id")["date"].min()
    common_start = first_dates.max()
    prices = prices[prices["date"] >= common_start].copy()
    base   = prices[prices["date"]==common_start].set_index("stock_id")["close"].rename("base")
    prices = prices.join(base, on="stock_id")
    prices["norm"]  = prices["close"] / prices["base"] * 100
    label_lkp = {sid: comp_df[comp_df["stock_id"]==sid]["label"].values[0]
                 for sid in sel_ids if sid in comp_df["stock_id"].values}
    prices["label"] = prices["stock_id"].map(label_lkp)

    trend = (
        alt.Chart(prices.dropna(subset=["norm","label"]))
        .mark_line(strokeWidth=2.2)
        .encode(
            x=alt.X("date:T", title="日期", axis=alt.Axis(format="%m/%d",tickCount=6,labelAngle=0)),
            y=alt.Y("norm:Q", title="相對指數（起始=100）", scale=alt.Scale(zero=False)),
            color=alt.Color("label:N", scale=c_scale, legend=alt.Legend(title="股票",orient="top")),
            tooltip=[
                alt.Tooltip("label:N",  title="股票"),
                alt.Tooltip("date:T",   title="日期",    format="%Y-%m-%d"),
                alt.Tooltip("close:Q",  title="收盤價",  format=".2f"),
                alt.Tooltip("norm:Q",   title="相對指數",format=".1f"),
            ],
        ).properties(height=340).interactive()
    )
    base_line = (alt.Chart(pd.DataFrame({"y":[100]}))
                 .mark_rule(color="#94a3b8",strokeDash=[4,3],strokeWidth=1).encode(y="y:Q"))
    st.altair_chart(
        alt.layer(trend,base_line).configure_axis(**_AXIS).configure_view(stroke=None),
        use_container_width=True, theme=None)
else:
    st.info("無法載入股價走勢資料。")
card_close()