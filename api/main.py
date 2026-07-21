"""api/main.py — FastAPI 主程式"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import data_health, market, rankings, stocks

app = FastAPI(
    title="StockLens API",
    description="台股量化分析與健康評估平台 API",
    version="1.0.0",
)

default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://web:3000",
]
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", ",".join(default_origins)).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(market.router)
app.include_router(rankings.router)
app.include_router(stocks.router)
app.include_router(data_health.router)


@app.get("/health")
def health():
    return {"status": "ok"}
