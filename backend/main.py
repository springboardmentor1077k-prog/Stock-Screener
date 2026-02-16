# Main FastAPI Application for Stock Screener
import os
from fastapi import FastAPI
from datetime import datetime
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware import Middleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.gzip import GZipMiddleware
import time
import logging
from .api.routers.screener import screener_router
from .api.routers.auth import auth_router
from .api.routers.portfolio import portfolio_router
from .api.routers.alerts import alerts_router
from .api.routers.data import data_router
from .api.routers.analytics import analytics_router
from .api.routers.ai_advice import ai_advice_router  # Handles /ai-advice and /explain-results endpoints

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log the request
        logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Process time: {process_time:.2f}s")
        
        return response


app = FastAPI(title="AI-Powered Stock Screener API", version="1.0.0")

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add custom request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware - Restrictive for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Default Streamlit port
        "http://localhost:3000",  # Common frontend port
        "http://127.0.0.1:8501",   # Alternative Streamlit address
        "http://localhost:*",      # Allow any localhost port (for development)
        os.getenv("FRONTEND_URL", "")  # From environment if set
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Specify allowed methods
    allow_headers=["*"],
)

# Trusted Host Middleware (security enhancement)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "*.localhost", "*.ngrok.io"]
)


# Include routers
app.include_router(screener_router, prefix="/api/v1/screener", tags=["screener"])
app.include_router(screener_router, prefix="/api/v1", tags=["screener-compat"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["portfolio"])
app.include_router(portfolio_router, prefix="/api/v1", tags=["portfolio-compat"])
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(data_router, prefix="/api/v1/data", tags=["data"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(ai_advice_router, prefix="/api/v1", tags=["ai"])

@app.get("/")
def read_root():
    """Root endpoint for the API"""
    from .core.utils import create_api_response
    return create_api_response(
        success=True,
        data={"version": "1.0.0", "status": "running"},
        message="Welcome to AI-Powered Stock Screener API"
    )


@app.get("/health")
def health_check():
    """Health check endpoint for the API"""
    from .core.utils import create_api_response
    from .database.connection import engine
    from sqlalchemy import text
    
    # Test database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)[:50]}..."  # Truncate error for security
    
    return create_api_response(
        success=True,
        data={"status": "healthy", "service": "AI-Powered Stock Screener API", "database": db_status},
        message="Service is healthy"
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle request validation errors"""
    from .core.utils import create_api_response
    return JSONResponse(
        status_code=422,
        content=create_api_response(success=False, error="Invalid input format", status_code=422),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    from .core.utils import create_api_response
    return JSONResponse(
        status_code=500,
        content=create_api_response(success=False, error="Internal server error occurred", status_code=500),
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    from .database.connection import engine
    logger.info("Shutting down application...")
    # Dispose of the database engine to close all connections
    engine.dispose()
    logger.info("Database connections closed.")