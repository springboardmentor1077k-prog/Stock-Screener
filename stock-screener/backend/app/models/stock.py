
from sqlalchemy import Column, Integer, String, BigInteger, Date
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Stock(Base):
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, index=True)
    sector = Column(String, index=True)
    industry = Column(String, index=True)
    exchange = Column(String, index=True)
    market_cap = Column(BigInteger)
    listing_date = Column(Date)
    status = Column(String, default="ACTIVE")


    fundamentals = relationship("Fundamentals", back_populates="stock", uselist=False)
    financials = relationship("Financials", back_populates="stock")
    portfolio_items = relationship("Portfolio", back_populates="stock")
    alerts = relationship("Alert", back_populates="stock")
