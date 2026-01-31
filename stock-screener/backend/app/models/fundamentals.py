
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Fundamentals(Base):
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), unique=True, nullable=False)
    
    market_cap = Column(BigInteger)
    pe_ratio = Column(Float)
    div_yield = Column(Float)
    current_price = Column(Float) # Added to support Price filtering
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    stock = relationship("Stock", back_populates="fundamentals")
