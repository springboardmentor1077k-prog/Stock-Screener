from fastapi import FastAPI
from backend.auth import router as auth_router
from backend.stocks import router as stock_router

app = FastAPI(title="Stock Screener API")

app.include_router(auth_router)
app.include_router(stock_router)
