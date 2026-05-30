#!/bin/sh
set -e

echo "StockLens ETL starting..."

echo "[1/3] 初始化資料庫"
python3 stock_etl.py --init-db

echo "[2/3] 抓取近 365 天股價"
python3 stock_etl.py --days 365

echo "[3/3] 計算量化因子與 K-means 分群"
python3 stock_factors.py --cluster

echo "StockLens ETL done."
