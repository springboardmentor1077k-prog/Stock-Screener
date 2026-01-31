
from typing import List, Optional, Literal, Union, Union
from pydantic import BaseModel
from datetime import datetime

# Fundamentals Schema
class FundamentalsBase(BaseModel):
    market_cap: int
    pe_ratio: float
    div_yield: float
    last_updated: Optional[datetime] = None

class FundamentalsCreate(FundamentalsBase):
    pass

class FundamentalsResponse(FundamentalsBase):
    id: int
    
    class Config:
        from_attributes = True

# Stock Schema
class StockBase(BaseModel):
    symbol: str
    company_name: str
    sector: str
    industry: str

class StockCreate(StockBase):
    pass

class StockResponse(StockBase):
    id: int
    fundamentals: Optional[FundamentalsResponse] = None

    class Config:
        from_attributes = True

# DSL Schemas
class FilterCondition(BaseModel):
    field: str
    operator: str
    value: Union[float, str]

class ScreenerQuery(BaseModel):
    action: str = "screen" # 'screen', 'get_price'
    target_symbol: Optional[str] = None
    conditions: List[FilterCondition] = []
    global_search: Optional[str] = None
