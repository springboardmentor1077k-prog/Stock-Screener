# Pydantic Models for API Schemas
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    BETWEEN = "between"
    IN = "in"
    CONTAINS = "contains"


class FinancialMetric(str, Enum):
    PE_RATIO = "pe_ratio"
    PEG_RATIO = "peg_ratio"
    EBITDA = "ebitda"
    FREE_CASH_FLOW = "free_cash_flow"
    PROMOTER_HOLDING = "promoter_holding"
    DEBT_TO_FREE_CASH_FLOW = "debt_to_free_cash_flow"
    REVENUE_GROWTH_YOY = "revenue_growth_yoy"
    EBITDA_GROWTH_YOY = "ebitda_growth_yoy"
    EARNINGS_GROWTH_YOY = "earnings_growth_yoy"
    CURRENT_PRICE = "current_price"
    MARKET_CAP = "market_cap"
    EPS = "eps"
    BOOK_VALUE = "book_value"
    ROE = "roe"
    ROA = "roa"
    DIVIDEND_YIELD = "dividend_yield"
    QUARTER_REVENUE = "quarter_revenue"
    QUARTER_EBITDA = "quarter_ebitda"
    QUARTER_NET_PROFIT = "quarter_net_profit"


class TimeFrame(str, Enum):
    LAST_QUARTER = "last_quarter"
    LAST_N_QUARTERS = "last_n_quarters"
    LAST_YEAR = "last_year"
    TTM = "ttm"  # Trailing Twelve Months


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"


class Condition(BaseModel):
    field: FinancialMetric
    operator: ConditionOperator
    value: Any
    time_frame: Optional[TimeFrame] = None


class ScreenerRule(BaseModel):
    conditions: List[Condition]
    logical_operator: str = "AND"  # AND or OR


class ScreenerDSL(BaseModel):
    name: str
    description: str
    rules: List[ScreenerRule]
    exchanges: Optional[List[Exchange]] = None
    sectors: Optional[List[str]] = None
    industries: Optional[List[str]] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class PortfolioItem(BaseModel):
    stock_id: str
    quantity: int
    avg_purchase_price: float


class PortfolioAddBySymbol(BaseModel):
    """Payload for adding a holding by human-friendly symbol."""

    symbol: str
    quantity: int
    avg_purchase_price: float


class AlertCreate(BaseModel):
    stock_id: str
    condition_type: str
    condition_value: float


class ScreenerResult(BaseModel):
    symbol: str
    company_name: str
    exchange: str
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    ebitda: Optional[float] = None
    free_cash_flow: Optional[float] = None
    current_price: Optional[float] = None
    # Add other fields as needed