from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.auth import router as auth_router
from backend.logic.routes import router as ai_router
from backend.api.portfolio import router as portfolio_router
from backend.api.alerts import router as alerts_router
from backend.api.stocks import router as stocks_router

app = FastAPI(title="AI Stock Screener")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(portfolio_router)
app.include_router(alerts_router)
app.include_router(stocks_router)
