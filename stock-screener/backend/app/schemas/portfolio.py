from typing import List, Optional
from pydantic import BaseModel
from app.schemas.stock import StockResponse

class PortfolioItemCreate(BaseModel):
    stock_id: int
    quantity: int = 0
    avg_price: float = 0.0

class PortfolioItemResponse(BaseModel):
    id: int
    stock: StockResponse
    quantity: int
    avg_price: float

    class Config:
        from_attributes = True
