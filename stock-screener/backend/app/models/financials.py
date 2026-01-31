
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Financials(Base):
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False)
    
    quarter_no = Column(Integer)
    fiscal_year = Column(Integer)
    revenue_generated = Column(Float)
    ebitda = Column(Float)
    net_profit = Column(Float)

    stock = relationship("Stock", back_populates="financials")
