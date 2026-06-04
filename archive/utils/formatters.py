"""utils/formatters.py — 格式化工具、健康分級、顏色常數"""

import pandas as pd

CATEGORY_LABELS = {
    "semiconductor": "半導體",
    "financial":     "金融",
    "etf":           "ETF",
    "electronics":   "電子",
    "shipping":      "航運",
    "telecom":       "電信",
    "other":         "其他",
}

HEALTH_COLORS = {
    "good":    "#149b55",
    "neutral": "#2563eb",
    "watch":   "#f59e0b",
    "risk":    "#ef4444",
}


def pct(value, digits=2):
    if pd.isna(value): return "-"
    return f"{value * 100:+.{digits}f}%"

def pct_plain(value, digits=2):
    if pd.isna(value): return "-"
    return f"{value * 100:.{digits}f}%"

def number(value, digits=1):
    if pd.isna(value): return "-"
    return f"{value:.{digits}f}"

def ratio(value):
    if pd.isna(value): return "-"
    return f"{value:.2f}"

def category_label(cat):
    return CATEGORY_LABELS.get(str(cat), str(cat))

def health_bucket(score):
    if pd.isna(score): return "neutral"
    if score >= 65:    return "good"
    if score >= 55:    return "neutral"
    if score >= 45:    return "watch"
    return "risk"

def health_label(score):
    return {"good":"健康較佳","neutral":"中性","watch":"需留意","risk":"風險較高"}[health_bucket(score)]

def score_color(score):
    return HEALTH_COLORS[health_bucket(score)]

def metric_class(value, positive_is_good=True):
    if pd.isna(value): return ""
    if positive_is_good: return "positive" if value >= 0 else "negative"
    return "negative" if value >= 0 else "positive"

def cluster_tag(factors_df):
    """依各 cluster 平均 health_score 排序，貼上強勢/穩健/弱勢標籤"""
    if "cluster_label" not in factors_df.columns: return {}
    valid = factors_df.dropna(subset=["cluster_label","health_score"])
    if valid.empty: return {}
    avg = valid.groupby("cluster_label")["health_score"].mean().sort_values(ascending=False)
    tags = ["強勢","穩健","弱勢"]
    return {int(k): tags[i] for i,k in enumerate(avg.index)}