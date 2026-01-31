
from typing import List, Any
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.stock import StockResponse, ScreenerQuery
from app.services.screener_service import ScreenerService

router = APIRouter()

@router.post("/search", response_model=List[StockResponse])
def search_stocks(
    *,
    db: Session = Depends(get_db),
    query: ScreenerQuery,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Execute a structured JSON query against the stock database.
    Protected endpoint.
    """
    return ScreenerService.execute_query(db, query)

@router.post("/parse", response_model=ScreenerQuery)
def parse_query(
    query_text: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Convert a natural language query string into a structured JSON query.
    Example: "PE < 15 and ROE > 20"
    """
    return ScreenerService.parse_natural_language(query_text, db, current_user.id)

@router.get("/history", response_model=List[Any])
def get_user_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get the history of queries run by the user.
    """
    from app.models.screeener_run import UserQuery
    return db.query(UserQuery).filter(UserQuery.user_id == current_user.id).order_by(UserQuery.timestamp.desc()).limit(50).all()

@router.get("/stocks-with-fundamentals", response_model=Any)
def get_stocks_with_fundamentals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all stocks with their fundamentals for the dashboard view.
    """
    from app.models.stock import Stock
    from app.models.fundamentals import Fundamentals
    
    stocks = db.query(Stock).all()
    result = []
    for stock in stocks:
        fund = stock.fundamentals
        result.append({
            "id": stock.id,
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "sector": stock.sector,
            "industry": stock.industry,
            "market_cap": fund.market_cap if fund else None,
            "pe_ratio": fund.pe_ratio if fund else None,
            "div_yield": fund.div_yield if fund else None,
            "current_price": fund.current_price if fund else None,
        })
    return {"data": result}

