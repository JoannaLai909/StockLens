# ── 第一階段：使用官方 Python 3.12 slim 映像檔 ──────────────────────────────
FROM python:3.12-slim

# 設定工作目錄（容器內的路徑）
WORKDIR /app

# 安裝系統套件（psycopg2-binary 需要 libpq）
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先複製 requirements 並安裝（利用 Docker layer cache 加速重建）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有程式碼進容器
COPY . .

# 複製並設定 entrypoint 腳本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 對外暴露 Streamlit 預設 port
EXPOSE 8501

# 啟動時執行 entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
