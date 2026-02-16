"""
Data API Router
Provides endpoints for fetching and ingesting financial data from external sources
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ...database.connection import get_db
from ...auth.jwt_handler import get_current_user
from ...models.database import User
from ...services.data_ingestion_service import ingest_stock_data, bulk_ingest_stocks
from ...services.data_fetcher_service import (
    get_stock_quote, 
    get_company_overview, 
    get_daily_time_series,
    get_income_statement,
    search_symbols
)

data_router = APIRouter()

@data_router.post("/ingest/stock")
def ingest_single_stock(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest data for a single stock symbol into the database.
    """
    try:
        success = ingest_stock_data(db, symbol)
        if success:
            return {"message": f"Successfully ingested data for stock {symbol}", "success": True}
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to ingest data for stock {symbol}"
            )
    except Exception as e:
        from ...core.exceptions import DatabaseException
        raise DatabaseException(detail=f"Error ingesting stock data: {str(e)}")

@data_router.post("/ingest/bulk")
def ingest_bulk_stocks(
    symbols: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest data for multiple stock symbols into the database.
    """
    try:
        results = bulk_ingest_stocks(db, symbols)
        return {"results": results}
    except Exception as e:
        from ...core.exceptions import DatabaseException
        raise DatabaseException(detail=f"Error ingesting bulk stock data: {str(e)}")

@data_router.get("/quote/{symbol}")
def get_stock_quote_endpoint(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time quote for a stock symbol from Alpha Vantage.
    """
    try:
        quote_data = get_stock_quote(symbol)
        if quote_data:
            return {"symbol": symbol, "quote": quote_data}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No quote data found for symbol {symbol}"
            )
    except Exception as e:
        from ...core.exceptions import APIServiceException
        raise APIServiceException(detail=f"Error fetching stock quote: {str(e)}")

@data_router.get("/overview/{symbol}")
def get_company_overview_endpoint(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get company overview information from Alpha Vantage.
    """
    try:
        overview_data = get_company_overview(symbol)
        if overview_data:
            return {"symbol": symbol, "overview": overview_data}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No overview data found for symbol {symbol}"
            )
    except Exception as e:
        from ...core.exceptions import APIServiceException
        raise APIServiceException(detail=f"Error fetching company overview: {str(e)}")

@data_router.get("/timeseries/daily/{symbol}")
def get_daily_time_series_endpoint(
    symbol: str,
    outputsize: str = "compact",  # compact (last 100 days) or full (20+ years)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get daily time series data for a stock symbol from Alpha Vantage.
    """
    try:
        if outputsize not in ["compact", "full"]:
            raise HTTPException(
                status_code=400,
                detail="Output size must be either 'compact' or 'full'"
            )
        
        time_series_data = get_daily_time_series(symbol, outputsize)
        if time_series_data:
            return {"symbol": symbol, "time_series": time_series_data, "outputsize": outputsize}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No time series data found for symbol {symbol}"
            )
    except Exception as e:
        from ...core.exceptions import APIServiceException
        raise APIServiceException(detail=f"Error fetching daily time series: {str(e)}")

@data_router.get("/income_statement/{symbol}")
def get_income_statement_endpoint(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get income statement data for a stock symbol from Alpha Vantage.
    """
    try:
        income_data = get_income_statement(symbol)
        if income_data:
            return {"symbol": symbol, "income_statement": income_data}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No income statement data found for symbol {symbol}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching income statement: {str(e)}"
        )

@data_router.get("/search/symbols")
def search_symbols_endpoint(
    keywords: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for stock symbols based on keywords from Alpha Vantage.
    """
    try:
        search_results = search_symbols(keywords)
        if search_results and "bestMatches" in search_results:
            return {"keywords": keywords, "results": search_results["bestMatches"]}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No symbols found matching '{keywords}'"
            )
    except Exception as e:
        from ...core.exceptions import APIServiceException
        raise APIServiceException(detail=f"Error searching symbols: {str(e)}")