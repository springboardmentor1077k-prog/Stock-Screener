# Database Models for Stock Screener
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Float, Boolean, Text, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user")
    alerts = relationship("Alert", back_populates="user")


class MasterStock(Base):
    __tablename__ = "master_stocks"
    
    stock_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    exchange = Column(String(10), nullable=False)
    sector = Column(String(50), index=True)
    industry = Column(String(100), index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fundamentals = relationship("Fundamental", back_populates="stock")
    quarterly_financials = relationship("QuarterlyFinancial", back_populates="stock")
    analyst_targets = relationship("AnalystTarget", back_populates="stock")
    portfolios = relationship("Portfolio", back_populates="stock")
    alerts = relationship("Alert", back_populates="stock")


class Fundamental(Base):
    __tablename__ = "fundamentals"
    
    fundamental_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_id = Column(String, ForeignKey("master_stocks.stock_id"), index=True)
    pe_ratio = Column(DECIMAL(10, 2), index=True)
    peg_ratio = Column(DECIMAL(10, 2), index=True)
    ebitda = Column(DECIMAL(15, 2), index=True)
    free_cash_flow = Column(DECIMAL(15, 2), index=True)
    promoter_holding = Column(DECIMAL(5, 2), index=True)
    debt_to_free_cash_flow = Column(DECIMAL(10, 2), index=True)
    revenue_growth_yoy = Column(DECIMAL(5, 2), index=True)
    ebitda_growth_yoy = Column(DECIMAL(5, 2), index=True)
    earnings_growth_yoy = Column(DECIMAL(5, 2), index=True)
    current_price = Column(DECIMAL(10, 2), index=True)
    market_cap = Column(DECIMAL(15, 2), index=True)
    eps = Column(DECIMAL(10, 2), index=True)
    book_value = Column(DECIMAL(10, 2), index=True)
    roe = Column(DECIMAL(5, 2), index=True)
    roa = Column(DECIMAL(5, 2), index=True)
    dividend_yield = Column(DECIMAL(5, 2), index=True)
    last_updated_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    stock = relationship("MasterStock", back_populates="fundamentals")


class QuarterlyFinancial(Base):
    __tablename__ = "quarterly_financials"
    
    quarterly_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_id = Column(String, ForeignKey("master_stocks.stock_id"), index=True)
    fiscal_year = Column(Integer, nullable=False)
    quarter_number = Column(Integer, nullable=False)  # 1-4
    revenue = Column(DECIMAL(15, 2))
    ebitda = Column(DECIMAL(15, 2))
    net_profit = Column(DECIMAL(15, 2))
    eps = Column(DECIMAL(10, 2))
    free_cash_flow = Column(DECIMAL(15, 2))
    reported_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = relationship("MasterStock", back_populates="quarterly_financials")


class AnalystTarget(Base):
    __tablename__ = "analyst_targets"
    
    target_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_id = Column(String, ForeignKey("master_stocks.stock_id"))
    target_price_low = Column(DECIMAL(10, 2))
    target_price_high = Column(DECIMAL(10, 2))
    target_price_avg = Column(DECIMAL(10, 2))
    current_price = Column(DECIMAL(10, 2))
    recommendation = Column(String(20))  # BUY, SELL, HOLD, etc.
    analyst_firm = Column(String(100))
    rating_date = Column(Date)
    next_earnings_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    stock = relationship("MasterStock", back_populates="analyst_targets")


class Portfolio(Base):
    __tablename__ = "portfolios"
    
    portfolio_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    stock_id = Column(String, ForeignKey("master_stocks.stock_id"), index=True)
    quantity = Column(Integer, nullable=False)
    avg_purchase_price = Column(DECIMAL(10, 2))
    purchase_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    stock = relationship("MasterStock", back_populates="portfolios")


class Alert(Base):
    __tablename__ = "alerts"
    
    alert_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    stock_id = Column(String, ForeignKey("master_stocks.stock_id"), index=True)
    condition_type = Column(String(50), nullable=False, index=True)  # e.g., 'PE_RATIO_BELOW', 'PRICE_ABOVE', etc.
    condition_value = Column(DECIMAL(10, 2))
    is_active = Column(Boolean, default=True, index=True)
    triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    stock = relationship("MasterStock", back_populates="alerts")


class ScreenerQuery(Base):
    __tablename__ = "screener_queries"
    
    query_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    query_name = Column(String(255), index=True)
    query_description = Column(Text)
    query_dsl = Column(Text)  # Store the structured DSL as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User")
