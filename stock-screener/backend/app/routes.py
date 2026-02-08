from typing import List, Any
from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.core import settings
from app.db import fetch_all, get_db
from app.schemas import (
    UserCreate, UserResponse, StockResponse, ScreenerQuery,
    PortfolioItemCreate, PortfolioItemResponse
)
from app.services import AuthService, ScreenerService, PortfolioService, get_current_user
from app.db import fetch_all

router = APIRouter()

# --- AUTH ROUTES ---

@router.post("/auth/signup", response_model=UserResponse)
def signup(*, conn = Depends(get_db), user_in: UserCreate) -> Any:
    return AuthService.signup(conn, user_in)

@router.post("/auth/login")
def login(conn = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    access_token = AuthService.login(conn, UserCreate(email=form_data.username, password=form_data.password))
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return {"access_token": access_token, "token_type": "bearer"}

# --- SCREENER ROUTES ---

@router.post("/screener/search", response_model=List[StockResponse])
def search_stocks(*, conn = Depends(get_db), query: ScreenerQuery, current_user = Depends(get_current_user)) -> Any:
    return ScreenerService.execute_query(conn, query)

@router.post("/screener/parse", response_model=ScreenerQuery)
def parse_query(query_text: str = Body(..., embed=True), conn = Depends(get_db), current_user = Depends(get_current_user)) -> Any:
    return ScreenerService.parse_natural_language(query_text, conn, current_user["id"])

@router.get("/screener/history", response_model=List[Any])
def get_user_history(conn = Depends(get_db), current_user = Depends(get_current_user)) -> Any:
    try:
        return fetch_all("SELECT * FROM userquery WHERE user_id = %s ORDER BY timestamp DESC LIMIT 50", (current_user["id"],))
    except Exception: return []

@router.get("/screener/stocks-with-fundamentals", response_model=Any)
def get_stocks_with_fundamentals(conn = Depends(get_db), current_user = Depends(get_current_user)) -> Any:
    stocks = fetch_all("SELECT s.id, s.symbol, s.company_name, s.sector, s.industry, f.market_cap, f.pe_ratio, f.div_yield, f.current_price FROM stock s LEFT JOIN fundamentals f ON s.id = f.stock_id", None)
    return {"data": stocks}

# --- PORTFOLIO ROUTES ---

@router.get("/portfolio", response_model=List[PortfolioItemResponse])
def get_portfolio(conn = Depends(get_db), current_user = Depends(get_current_user)) -> Any:
    return PortfolioService.get_user_portfolio(conn, current_user["id"])

@router.post("/portfolio", response_model=PortfolioItemResponse)
def add_to_portfolio(*, conn = Depends(get_db), item_in: PortfolioItemCreate, current_user = Depends(get_current_user)) -> Any:
    return PortfolioService.add_stock(conn, current_user["id"], item_in)

@router.delete("/portfolio/{stock_id}")
def remove_from_portfolio(stock_id: int, conn = Depends(get_db), current_user = Depends(get_current_user)) -> Any:
    return PortfolioService.remove_stock(conn, current_user["id"], stock_id)
