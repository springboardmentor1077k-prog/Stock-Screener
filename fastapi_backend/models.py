from typing import List, Optional, Any
from pydantic import BaseModel, Field

class ScreenRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The screening query or natural language sentence")
    sector: str = "All"
    strong_only: bool = False
    market_cap: str = "Any"

class StockData(BaseModel):
    symbol: str
    company_name: str
    price: float
    sector: str
    market_cap: float
    pe_ratio: Optional[float] = None

class ScreenResponse(BaseModel):
    status: str = "success"
    data: List[StockData]
    cached: bool = False
    latency_ms: int = 0

class PortfolioItem(BaseModel):
    symbol: str
    quantity: int
    avg_buy_price: float
    current_price: float
    company_name: str
    profit_loss: float

class PortfolioResponse(BaseModel):
    status: str = "success"
    data: List[PortfolioItem]

class PortfolioAddRequest(BaseModel):
    symbol: str = Field(..., pattern="^[A-Z]{1,10}$")
    quantity: int = Field(..., gt=0)
    avg_buy_price: float = Field(..., gt=0)

class AlertCreateRequest(BaseModel):
    symbol: str = Field(..., pattern="^[A-Z]{1,10}$")
    condition: str = Field(..., description="'Above Price' or 'Below Price'")
    value: float = Field(..., gt=0)

class AlertData(BaseModel):
    id: int
    user_id: int
    portfolio_id: int
    metric: str
    operator: str
    threshold: float
    is_active: bool

class AlertResponse(BaseModel):
    status: str = "success"
    data: List[AlertData]

class AlertCheckResponse(BaseModel):
    status: str = "success"
    message: str
    metrics: dict
    data: List[Any]
