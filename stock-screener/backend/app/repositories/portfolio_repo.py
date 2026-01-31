
from typing import List
from sqlalchemy.orm import Session
from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioItemCreate

class PortfolioRepository:
    @staticmethod
    def add_to_portfolio(db: Session, user_id: int, item_in: PortfolioItemCreate) -> Portfolio:
        item = Portfolio(
            user_id=user_id, 
            stock_id=item_in.stock_id,
            quantity=item_in.quantity,
            avg_price=item_in.avg_price
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_portfolio(db: Session, user_id: int) -> List[Portfolio]:
        return db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

    @staticmethod
    def remove_from_portfolio(db: Session, user_id: int, stock_id: int) -> bool:
        item = db.query(Portfolio).filter(Portfolio.user_id == user_id, Portfolio.stock_id == stock_id).first()
        if item:
            db.delete(item)
            db.commit()
            return True
        return False
