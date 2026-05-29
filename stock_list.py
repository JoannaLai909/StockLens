# stock_list.py
# 股票清單與產業分類
# 成員 A：Day 1-3
# -------------------------------------------------------
# 共 30 支

STOCK_LIST = [
    # ETF
    {"stock_id": "0050", "name": "元大台灣50", "category": "etf", "market": "TSE"},
    {"stock_id": "0056", "name": "元大高股息", "category": "etf", "market": "TSE"},
    {"stock_id": "00878", "name": "國泰永續高股息", "category": "etf", "market": "TSE"},
    {"stock_id": "006208", "name": "富邦台50", "category": "etf", "market": "TSE"},
    {"stock_id": "00713", "name": "元大台灣高息低波", "category": "etf", "market": "TSE"},

    # 半導體
    {"stock_id": "2330", "name": "台積電", "category": "semiconductor", "market": "TSE"},
    {"stock_id": "2303", "name": "聯電", "category": "semiconductor", "market": "TSE"},
    {"stock_id": "2454", "name": "聯發科", "category": "semiconductor", "market": "TSE"},
    {"stock_id": "2379", "name": "瑞昱", "category": "semiconductor", "market": "TSE"},
    {"stock_id": "3034", "name": "聯詠", "category": "semiconductor", "market": "TSE"},
    {"stock_id": "3711", "name": "日月光投控", "category": "semiconductor", "market": "TSE"},
    {"stock_id": "3443", "name": "創意", "category": "semiconductor", "market": "TSE"},

    # 金融
    {"stock_id": "2881", "name": "富邦金", "category": "financial", "market": "TSE"},
    {"stock_id": "2882", "name": "國泰金", "category": "financial", "market": "TSE"},
    {"stock_id": "2891", "name": "中信金", "category": "financial", "market": "TSE"},
    {"stock_id": "2886", "name": "兆豐金", "category": "financial", "market": "TSE"},
    {"stock_id": "2884", "name": "玉山金", "category": "financial", "market": "TSE"},
    {"stock_id": "2885", "name": "元大金", "category": "financial", "market": "TSE"},
    {"stock_id": "2880", "name": "華南金", "category": "financial", "market": "TSE"},

    # 電子 / 代工
    {"stock_id": "2317", "name": "鴻海", "category": "electronics", "market": "TSE"},
    {"stock_id": "2354", "name": "鴻準", "category": "electronics", "market": "TSE"},
    {"stock_id": "2382", "name": "廣達", "category": "electronics", "market": "TSE"},
    {"stock_id": "3231", "name": "緯創", "category": "electronics", "market": "TSE"},
    {"stock_id": "4938", "name": "和碩", "category": "electronics", "market": "TSE"},

    # 航運
    {"stock_id": "2603", "name": "長榮", "category": "shipping", "market": "TSE"},
    {"stock_id": "2609", "name": "陽明", "category": "shipping", "market": "TSE"},
    {"stock_id": "2615", "name": "萬海", "category": "shipping", "market": "TSE"},

    # 電信
    {"stock_id": "2412", "name": "中華電", "category": "telecom", "market": "TSE"},
    {"stock_id": "3045", "name": "台灣大", "category": "telecom", "market": "TSE"},
    {"stock_id": "4904", "name": "遠傳", "category": "telecom", "market": "TSE"},
]

# 給其他模組 import 用的快速查表
STOCK_IDS = [s["stock_id"] for s in STOCK_LIST]

CATEGORY_MAP = {s["stock_id"]: s["category"] for s in STOCK_LIST}
NAME_MAP     = {s["stock_id"]: s["name"]     for s in STOCK_LIST}

if __name__ == "__main__":
    print(f"共 {len(STOCK_LIST)} 支股票")
    for s in STOCK_LIST:
        print(f"  {s['stock_id']}  {s['name']:<10}  {s['category']}")
