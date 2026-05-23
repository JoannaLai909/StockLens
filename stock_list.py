# stock_list.py
# 股票清單與產業分類
# 成員 A：Day 1-3
# -------------------------------------------------------
# 共 10 支，免費版 FinMind 速率限制建議不超過 10 支

STOCK_LIST = [
    # ETF
    {"stock_id": "0050", "name": "元大台灣50",       "category": "etf",           "market": "TSE"},
    {"stock_id": "0056", "name": "元大高股息",        "category": "etf",           "market": "TSE"},

    # 半導體
    {"stock_id": "2330", "name": "台積電",            "category": "semiconductor", "market": "TSE"},
    {"stock_id": "2303", "name": "聯電",              "category": "semiconductor", "market": "TSE"},
    {"stock_id": "2379", "name": "瑞昱",              "category": "semiconductor", "market": "TSE"},

    # 金融
    {"stock_id": "2882", "name": "國泰金",            "category": "financial",     "market": "TSE"},
    {"stock_id": "2881", "name": "富邦金",            "category": "financial",     "market": "TSE"},
    {"stock_id": "2891", "name": "中信金",            "category": "financial",     "market": "TSE"},

    # 其他（科技 / 電子）
    {"stock_id": "2317", "name": "鴻海",              "category": "other",         "market": "TSE"},
    {"stock_id": "2454", "name": "聯發科",            "category": "semiconductor", "market": "TSE"},
]

# 給其他模組 import 用的快速查表
STOCK_IDS = [s["stock_id"] for s in STOCK_LIST]

CATEGORY_MAP = {s["stock_id"]: s["category"] for s in STOCK_LIST}
NAME_MAP     = {s["stock_id"]: s["name"]     for s in STOCK_LIST}

if __name__ == "__main__":
    print(f"共 {len(STOCK_LIST)} 支股票")
    for s in STOCK_LIST:
        print(f"  {s['stock_id']}  {s['name']:<10}  {s['category']}")
