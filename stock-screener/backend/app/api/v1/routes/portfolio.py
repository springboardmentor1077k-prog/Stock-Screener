
from typing import List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.portfolio import PortfolioItemCreate, PortfolioItemResponse
from app.services.portfolio_service import PortfolioService

router = APIRouter()

@router.get("/", response_model=List[PortfolioItemResponse])
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return PortfolioService.get_user_portfolio(db, current_user.id)

@router.post("/", response_model=PortfolioItemResponse)
def add_to_portfolio(
    *,
    db: Session = Depends(get_db),
    item_in: PortfolioItemCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    return PortfolioService.add_stock(db, current_user.id, item_in)

@router.delete("/{stock_id}")
def remove_from_portfolio(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return PortfolioService.remove_stock(db, current_user.id, stock_id)
