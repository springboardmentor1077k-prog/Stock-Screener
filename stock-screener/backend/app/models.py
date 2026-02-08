from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, BigInteger, Text, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Stock(Base):
    __tablename__ = "stock"
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

class Fundamentals(Base):
    __tablename__ = "fundamentals"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), unique=True, nullable=False)
    market_cap = Column(BigInteger)
    pe_ratio = Column(Float)
    div_yield = Column(Float)
    current_price = Column(Float)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    stock = relationship("Stock", back_populates="fundamentals")

class Financials(Base):
    __tablename__ = "financials"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False)
    quarter_no = Column(Integer)
    fiscal_year = Column(Integer)
    revenue_generated = Column(Float)
    ebitda = Column(Float)
    net_profit = Column(Float)

    stock = relationship("Stock", back_populates="financials")

class Portfolio(Base):
    __tablename__ = "portfolio"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False)
    quantity = Column(Integer, default=0)
    avg_price = Column(Float, default=0.0)

    stock = relationship("Stock", back_populates="portfolio_items")

class Alert(Base):
    __tablename__ = "alert"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False)
    target_price = Column(Float, nullable=False)
    condition = Column(String, nullable=False) # "Above" or "Below"

    stock = relationship("Stock", back_populates="alerts")

class UserQuery(Base):
    __tablename__ = "user_queries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    raw_query_text = Column(Text, nullable=False)
    action = Column(String)
    parsed_dsl = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
