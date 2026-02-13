import sys
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback

# Add current directory to path for absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logging_config import logger
from utils.exceptions import AppBaseException, ErrorResponse
from models import (
    ScreenRequest, ScreenResponse, 
    PortfolioResponse, PortfolioAddRequest,
    AlertCreateRequest, AlertResponse, AlertCheckResponse
)
from services.screener import screener_service
from services.portfolio import portfolio_service
from services.alerts import alerts_service

app = FastAPI(
    title="Stock Analytics Platform API",
    description="Production-grade FastAPI backend for stock screening, portfolio management, and alerts.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Centralized Exception Handling ---

@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException):
    logger.error(f"App Error: {exc.error_code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Invalid input provided",
            details=exc.errors()
        ).dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            details=None
        ).dict()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log full stack trace internally
    logger.error(f"Unhandled Exception: {str(exc)}\n{traceback.format_exc()}")
    
    # Return sanitized response to UI
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="System error. Please try again later.",
            details=None
        ).dict()
    )

# --- Routes ---

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/screen", response_model=ScreenResponse)
async def screen_stocks(request: ScreenRequest):
    result = screener_service.screen(
        query=request.query,
        sector=request.sector,
        strong_only=request.strong_only,
        market_cap_filter=request.market_cap
    )
    return result

@app.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    # In a real app, we'd get user_id from auth token
    data = portfolio_service.get_portfolio(user_id=1)
    return {"status": "success", "data": data}

@app.post("/portfolio", response_model=dict)
async def add_to_portfolio(request: PortfolioAddRequest):
    result = portfolio_service.add_to_portfolio(
        symbol=request.symbol,
        quantity=request.quantity,
        avg_buy_price=request.avg_buy_price,
        user_id=1
    )
    return result

@app.get("/alerts", response_model=AlertResponse)
async def get_alerts():
    data = alerts_service.get_alerts(portfolio_id=1)
    return {"status": "success", "data": data}

@app.post("/alerts", response_model=dict)
async def create_alert(request: AlertCreateRequest):
    result = alerts_service.create_alert(
        symbol=request.symbol,
        condition=request.condition,
        value=request.value,
        user_id=1,
        portfolio_id=1
    )
    return result

@app.post("/alerts/checks", response_model=AlertCheckResponse)
async def check_alerts():
    result = alerts_service.check_alerts(portfolio_id=1)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
