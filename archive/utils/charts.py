"""utils/charts.py — 所有 Altair 圖表"""

import math
import altair as alt
import pandas as pd
import streamlit as st

from utils.formatters import HEALTH_COLORS, health_label, score_color, number, category_label


_LEGEND_HTML = """
<div style="display:flex;justify-content:center;gap:1.8rem;color:#223a5c;
            font-size:.82rem;margin-top:.2rem;font-family:-apple-system,sans-serif;">
    <span><i style="display:inline-block;width:9px;height:9px;border-radius:50%;
              background:#149b55;margin-right:.4rem;vertical-align:middle;"></i>健康較佳</span>
    <span><i style="display:inline-block;width:9px;height:9px;border-radius:50%;
              background:#2563eb;margin-right:.4rem;vertical-align:middle;"></i>中性</span>
    <span><i style="display:inline-block;width:9px;height:9px;border-radius:50%;
              background:#f59e0b;margin-right:.4rem;vertical-align:middle;"></i>需留意</span>
    <span><i style="display:inline-block;width:9px;height:9px;border-radius:50%;
              background:#ef4444;margin-right:.4rem;vertical-align:middle;"></i>風險較高</span>
</div>
"""

_AXIS = dict(grid=True, gridColor="#dde5f0", labelColor="#334155", titleColor="#334155",
             labelFontSize=11, titleFontSize=11)


def _auto_domain(series, pad=0.2, min_span=2):
    lo, hi = series.min(), series.max()
    span = max(hi - lo, min_span)
    p = span * pad
    return [math.floor((lo - p) * 10) / 10, math.ceil((hi + p) * 10) / 10]


def _scatter(chart_df, height, x_dom, y_dom, color_domain, color_range):
    mid_y = y_dom[0] + (y_dom[1] - y_dom[0]) * 0.35
    vline = alt.Chart(pd.DataFrame({"x":[0]})).mark_rule(color="#9db0c7",strokeDash=[5,4]).encode(x="x:Q")
    hline = alt.Chart(pd.DataFrame({"y":[mid_y]})).mark_rule(color="#9db0c7",strokeDash=[5,4]).encode(y="y:Q")
    pts   = (
        alt.Chart(chart_df)
        .mark_circle(size=85, opacity=.87, stroke="white", strokeWidth=1.5)
        .encode(
            x=alt.X("報酬率:Q", title="報酬率 (%)", scale=alt.Scale(domain=x_dom)),
            y=alt.Y("波動率:Q", title="波動率 (%)", scale=alt.Scale(domain=y_dom)),
            color=alt.Color("狀態:N",
                scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
            tooltip=[
                alt.Tooltip("股票:N",      title="股票"),
                alt.Tooltip("報酬率:Q",    title="20日報酬率", format=".2f"),
                alt.Tooltip("波動率:Q",    title="20日波動率", format=".2f"),
                alt.Tooltip("health_score:Q", title="健康分數", format=".1f"),
                alt.Tooltip("category:N", title="產業"),
            ],
        )
    )
    return (
        alt.layer(vline, hline, pts)
        .properties(height=height, background="#ffffff")
        .configure_axis(**_AXIS)
        .configure_view(stroke=None)
    )


def render_health_scatter(factors):
    df = factors.dropna(subset=["return_20d","volatility_20d"]).copy()
    if df.empty:
        st.info("目前無資料。")
        return
    df["報酬率"]  = df["return_20d"]    * 100
    df["波動率"]  = df["volatility_20d"] * 100
    df["狀態"]    = df["health_score"].apply(health_label)
    df["股票"]    = df["stock_id"] + " " + df["name"]

    cd = ["健康較佳","中性","需留意","風險較高"]
    cr = [HEALTH_COLORS["good"],HEALTH_COLORS["neutral"],
          HEALTH_COLORS["watch"],HEALTH_COLORS["risk"]]

    # 離群值 clip：超過 p5/p95 的 5% 才擴展，避免單一離群值拉爆 scale
    x_vals = df["報酬率"]
    p5, p95 = x_vals.quantile(.05), x_vals.quantile(.95)
    span    = max(p95 - p5, 4)
    x_dom   = [math.floor(p5 - span*.2), math.ceil(p95 + span*.2)]
    y_dom   = _auto_domain(df["波動率"])

    st.altair_chart(_scatter(df, 248, x_dom, y_dom, cd, cr), use_container_width=True, theme=None)
    st.markdown(_LEGEND_HTML, unsafe_allow_html=True)

    with st.expander("🔍 放大散點圖"):
        st.altair_chart(_scatter(df, 480, x_dom, y_dom, cd, cr), use_container_width=True, theme=None)
        st.markdown(_LEGEND_HTML, unsafe_allow_html=True)


def render_industry_chart(industry):
    if industry.empty:
        st.info("目前無資料。")
        return
    df = industry.copy()
    df["產業"]      = df["category"].apply(category_label)
    df["score_text"]= df["avg_health_score"].map(lambda x: number(x,1))
    df["顏色"]      = df["avg_health_score"].apply(score_color)

    bars = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("avg_health_score:Q", title="健康分數 (0-100)", scale=alt.Scale(domain=[0,100])),
            y=alt.Y("產業:N", sort="-x", title=None),
            color=alt.Color("顏色:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("產業:N",           title="產業"),
                alt.Tooltip("avg_health_score:Q",title="平均健康分數",format=".1f"),
                alt.Tooltip("stock_count:Q",     title="股票數"),
                alt.Tooltip("avg_return_20d:Q",  title="平均20日報酬",format=".2%"),
            ],
        )
    )
    text = (
        alt.Chart(df)
        .mark_text(align="left", dx=5, fontWeight="bold", fontSize=12)
        .encode(
            x="avg_health_score:Q",
            y=alt.Y("產業:N", sort="-x"),
            text="score_text:N",
            color=alt.Color("顏色:N", scale=None, legend=None),
        )
    )
    st.altair_chart(
        (bars+text)
        .properties(height=248, background="#ffffff")
        .configure_axis(**_AXIS)
        .configure_view(stroke=None),
        use_container_width=True, theme=None,
    )


def render_price_chart(prices, days=126):
    if prices.empty:
        st.info("此股票沒有股價資料。")
        return
    df = prices.tail(days).copy()
    st.altair_chart(
        alt.Chart(df)
        .mark_line(color="#0f6fe8", strokeWidth=2.2)
        .encode(
            x=alt.X("date:T", title=None, axis=alt.Axis(format="%Y-%m", tickCount=6)),
            y=alt.Y("close:Q", title=None, scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("date:T",  title="日期",  format="%Y-%m-%d"),
                alt.Tooltip("close:Q", title="收盤價", format=".2f"),
            ],
        )
        .properties(height=180, background="#ffffff")
        .configure_axis(**_AXIS)
        .configure_view(stroke=None),
        use_container_width=True, theme=None,
    )


def render_volume_chart(prices, days=126):
    if prices.empty: return
    df = prices.tail(days).copy()
    df["color"] = df["close"].diff().apply(lambda x: "#149b55" if x >= 0 else "#ef4444")
    st.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("date:T", title=None, axis=alt.Axis(format="%Y-%m", tickCount=6)),
            y=alt.Y("volume:Q", title="成交量", axis=alt.Axis(format=".2s")),
            color=alt.Color("color:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("date:T",   title="日期",  format="%Y-%m-%d"),
                alt.Tooltip("volume:Q", title="成交量", format=","),
            ],
        )
        .properties(height=110, background="#ffffff")
        .configure_axis(**_AXIS)
        .configure_view(stroke=None),
        use_container_width=True, theme=None,
    )