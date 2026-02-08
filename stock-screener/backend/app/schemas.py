from typing import List, Optional, Literal, Union
from pydantic import BaseModel, EmailStr
from datetime import datetime

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool

# --- STOCK/FUNDAMENTALS SCHEMAS ---
class FundamentalsBase(BaseModel):
    market_cap: Optional[int] = None
    pe_ratio: Optional[float] = None
    div_yield: Optional[float] = None
    last_updated: Optional[datetime] = None

class FundamentalsResponse(FundamentalsBase):
    id: int

class StockBase(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None

class StockResponse(StockBase):
    id: int
    fundamentals: Optional[FundamentalsResponse] = None

# --- PORTFOLIO SCHEMAS ---
class PortfolioItemCreate(BaseModel):
    stock_id: int
    quantity: int = 0
    avg_price: float = 0.0

class PortfolioItemResponse(BaseModel):
    id: int
    user_id: int
    stock_id: int
    quantity: int
    avg_price: float
    stock: StockResponse

# --- DSL SCHEMAS ---
class FilterCondition(BaseModel):
    field: str
    operator: str
    value: Union[float, str]

class ScreenerQuery(BaseModel):
    action: str = "screen"
    target_symbol: Optional[str] = None
    conditions: List[FilterCondition] = []
    global_search: Optional[str] = None
