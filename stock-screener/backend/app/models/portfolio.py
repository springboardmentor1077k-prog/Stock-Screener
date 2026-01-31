
from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Portfolio(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False)
    
    quantity = Column(Integer, default=0)
    avg_price = Column(Float, default=0.0)

    user = relationship("User", back_populates="portfolio")
    stock = relationship("Stock", back_populates="portfolio_items")
