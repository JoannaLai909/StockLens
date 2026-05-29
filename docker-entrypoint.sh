#!/bin/bash
# 任何指令失敗就立刻停止，避免帶著錯誤繼續跑
set -e

echo "======================================"
echo "  StockLens 啟動中..."
echo "======================================"

# ── 1. 等待 PostgreSQL 就緒 ───────────────────────────────────────────────────
echo ""
echo "[1/4] 等待資料庫就緒..."

until python3 - <<'EOF'
import psycopg2, os, sys
try:
    psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "stockdb"),
        user=os.getenv("DB_USER", "stock_user"),
        password=os.getenv("DB_PASSWORD"),
    ).close()
    sys.exit(0)
except Exception:
    sys.exit(1)
EOF
do
    echo "  資料庫尚未就緒，5 秒後重試..."
    sleep 5
done

echo "  ✅ 資料庫已連線！"

# ── 2. 初始化資料庫（建表 + 寫入股票清單）─────────────────────────────────────
echo ""
echo "[2/4] 初始化資料庫..."
python3 stock_etl.py --init-db
echo "  ✅ 資料庫初始化完成"

# ── 3. 執行 ETL 抓取股價資料 ──────────────────────────────────────────────────
echo ""
echo "[3/4] 執行 ETL（抓取近 90 天股價）..."
python3 stock_etl.py --days 90
echo "  ✅ ETL 完成"

# ── 4. 計算量化因子 ────────────────────────────────────────────────────────────
echo ""
echo "[4/4] 計算量化因子..."
python3 stock_factors.py
echo "  ✅ 因子計算完成"

# ── 啟動 Streamlit Dashboard ──────────────────────────────────────────────────
echo ""
echo "======================================"
echo "  🚀 啟動 Dashboard（port 8501）"
echo "======================================"

exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
