"""utils/pdf_report.py — 用 reportlab 產生個股分析 PDF 報告（支援中文）"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── 字型註冊：嘗試找系統內建的中文字型 ───────────────────────────────────────
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKtc-Regular.otf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",            # macOS
    "C:/Windows/Fonts/msjh.ttc",                     # Windows
]

_FONT_NAME = "Helvetica"  # fallback（不支援中文但不會崩）

for _path in _FONT_CANDIDATES:
    if os.path.exists(_path):
        try:
            pdfmetrics.registerFont(TTFont("CJK", _path))
            _FONT_NAME = "CJK"
        except Exception:
            pass
        break


# ── 顏色 ──────────────────────────────────────────────────────────────────────
_BLUE   = colors.HexColor("#0f6fe8")
_GREEN  = colors.HexColor("#149b55")
_RED    = colors.HexColor("#ef4444")
_ORANGE = colors.HexColor("#f59e0b")
_LIGHT  = colors.HexColor("#f0f4f9")
_BORDER = colors.HexColor("#dbe4ef")
_TEXT   = colors.HexColor("#0b1f3f")
_MUTED  = colors.HexColor("#5d6d86")
_WHITE  = colors.white


def _style(size=10, bold=False, color=None, align="LEFT"):
    return ParagraphStyle(
        "s",
        fontName=_FONT_NAME + ("-Bold" if bold and _FONT_NAME != "Helvetica" else ""),
        fontSize=size,
        textColor=color or _TEXT,
        alignment={"LEFT":0,"CENTER":1,"RIGHT":2}.get(align,0),
        leading=size*1.45,
    )


def generate_pdf(
    stock_id, name, category, market,
    latest_date, latest_close,
    r20, r60, vol, drawdown, vol_ratio, score,
    cluster_text, health_lbl,
) -> bytes:
    """回傳 PDF bytes，供 st.download_button 使用。"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    fn  = _FONT_NAME
    story = []

    # ── 標題區 ──────────────────────────────────────────────────────────────
    story.append(Paragraph("StockLens 個股分析報告", _style(20, bold=True, color=_BLUE)))
    story.append(Spacer(1, .3*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_BLUE))
    story.append(Spacer(1, .4*cm))

    # ── 基本資訊 ─────────────────────────────────────────────────────────────
    story.append(Paragraph("基本資訊", _style(13, bold=True, color=_BLUE)))
    story.append(Spacer(1, .25*cm))

    info_data = [
        ["股票代號", stock_id,    "股票名稱", name],
        ["產業分類", category,    "市場別",   market],
        ["最新資料日", str(latest_date), "收盤價", f"{float(latest_close):.2f}"],
        ["K-means 分群", cluster_text, "", ""],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 4.5*cm, 3.5*cm, 4.5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",    (0,0),(-1,-1), fn),
        ("FONTSIZE",    (0,0),(-1,-1), 10),
        ("TEXTCOLOR",   (0,0),(-1,-1), _TEXT),
        ("TEXTCOLOR",   (0,0),(0,-1),  _MUTED),
        ("TEXTCOLOR",   (2,0),(2,-1),  _MUTED),
        ("FONTNAME",    (0,0),(0,-1),  fn),
        ("BACKGROUND",  (0,0),(-1,-1), _LIGHT),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[_WHITE, _LIGHT]),
        ("GRID",        (0,0),(-1,-1), .5, _BORDER),
        ("PADDING",     (0,0),(-1,-1), 7),
        ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, .5*cm))

    # ── 量化因子 ──────────────────────────────────────────────────────────────
    story.append(Paragraph("量化因子", _style(13, bold=True, color=_BLUE)))
    story.append(Spacer(1, .25*cm))

    def _pct(v):
        try: return f"{float(v)*100:+.2f}%"
        except: return "-"
    def _pct_plain(v):
        try: return f"{float(v)*100:.2f}%"
        except: return "-"
    def _num(v):
        try: return f"{float(v):.1f}"
        except: return "-"
    def _ratio(v):
        try: return f"{float(v):.2f}"
        except: return "-"

    def _color_cell(v, good_if_pos=True):
        try:
            fv = float(v)
            if good_if_pos: return _GREEN if fv >= 0 else _RED
            return _RED if fv >= 0 else _GREEN
        except: return _MUTED

    factor_rows = [
        ["指標", "數值", "說明"],
        ["20 日報酬率",  _pct(r20),       "近 20 個交易日的價格變動率"],
        ["60 日報酬率",  _pct(r60),       "近 60 個交易日的價格變動率"],
        ["波動率",       _pct_plain(vol), "20 日日報酬率標準差"],
        ["最大回撤",     _pct(drawdown),  "近 60 日最大跌幅"],
        ["成交量倍率",   _ratio(vol_ratio),"5日均量 / 20日均量"],
        ["健康分數",     _num(score)+"/100","綜合評分（0–100，越高越好）"],
    ]

    col_w = [4*cm, 3.5*cm, 8*cm]
    ft = Table(factor_rows, colWidths=col_w)
    style_cmds = [
        ("FONTNAME",   (0,0),(-1,-1), fn),
        ("FONTSIZE",   (0,0),(-1,-1), 10),
        ("BACKGROUND", (0,0),(-1,0),  _BLUE),
        ("TEXTCOLOR",  (0,0),(-1,0),  _WHITE),
        ("FONTNAME",   (0,0),(-1,0),  fn),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[_WHITE,_LIGHT]),
        ("GRID",       (0,0),(-1,-1), .5, _BORDER),
        ("PADDING",    (0,0),(-1,-1), 7),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("TEXTCOLOR",  (0,1),(0,-1),  _MUTED),
    ]
    # 數值欄染色
    val_colors = [
        _color_cell(r20, True),
        _color_cell(r60, True),
        _BLUE,
        _color_cell(drawdown, False),
        _ORANGE,
        _GREEN if (not str(score) in ["-",""] and float(score) >= 55) else _RED,
    ]
    for i, c in enumerate(val_colors, start=1):
        style_cmds.append(("TEXTCOLOR", (1,i),(1,i), c))
        style_cmds.append(("FONTNAME",  (1,i),(1,i), fn))

    ft.setStyle(TableStyle(style_cmds))
    story.append(ft)
    story.append(Spacer(1, .5*cm))

    # ── 健康狀態 ──────────────────────────────────────────────────────────────
    story.append(Paragraph("健康狀態摘要", _style(13, bold=True, color=_BLUE)))
    story.append(Spacer(1, .25*cm))
    story.append(Paragraph(
        f"目前健康狀態評級為「{health_lbl}」，K-means 分群為「{cluster_text}」。"
        "請搭配報酬率、波動率、最大回撤與成交量變化一起判斷，不建議只看單一指標。",
        _style(10, color=_TEXT),
    ))
    story.append(Spacer(1, .4*cm))
    story.append(HRFlowable(width="100%", thickness=.5, color=_BORDER))
    story.append(Spacer(1, .3*cm))
    story.append(Paragraph(
        "⚠️ 本報告僅供課程展示與研究參考，不構成任何投資建議。",
        _style(9, color=_MUTED),
    ))

    doc.build(story)
    return buf.getvalue()