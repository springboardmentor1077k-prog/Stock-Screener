from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import stocks, alerts, portfolio, auth

app = FastAPI(
    title="StockSense AI API",
    description="AI-Powered Stock Screening and Portfolio Management",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers with API versioning
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["Stocks"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to StockSense AI API",
        "docs": "/docs",
        "disclaimer": "This platform is for educational purposes only. Not financial advice.",
        "endpoints": {
            "auth": "/api/v1/auth",
            "stocks": "/api/v1/stocks",
            "portfolio": "/api/v1/portfolio",
            "alerts": "/api/v1/alerts"
        }
    }