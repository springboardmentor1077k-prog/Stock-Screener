
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.portfolio_repo import PortfolioRepository
from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioItemCreate

class PortfolioService:
    @staticmethod
    def add_stock(db: Session, user_id: int, item_in: PortfolioItemCreate) -> Portfolio:
        # Check if already exists?
        existing = db.query(Portfolio).filter(Portfolio.user_id == user_id, Portfolio.stock_id == item_in.stock_id).first()
        if existing:
             # Basic update logic could go here, for now just fail
             raise HTTPException(status_code=400, detail="Stock already in portfolio")
        return PortfolioRepository.add_to_portfolio(db, user_id, item_in)

    @staticmethod
    def get_user_portfolio(db: Session, user_id: int) -> List[Portfolio]:
        return PortfolioRepository.get_portfolio(db, user_id)

    @staticmethod
    def remove_stock(db: Session, user_id: int, stock_id: int):
        success = PortfolioRepository.remove_from_portfolio(db, user_id, stock_id)
        if not success:
             raise HTTPException(status_code=404, detail="Stock not found in portfolio")
        return {"status": "success"}
