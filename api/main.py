"""api/main.py — FastAPI 主程式"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import market, rankings, stocks

app = FastAPI(
    title="StockLens API",
    description="台股量化分析平台 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://web:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(market.router)
app.include_router(rankings.router)
app.include_router(stocks.router)


@app.get("/health")
def health():
    return {"status": "ok"}