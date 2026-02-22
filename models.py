from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Index, func, Boolean
from sqlalchemy.orm import relationship
from .database import Base

# ==========================================
# 1. User Management (RBAC)
# ==========================================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")  # 'admin' or 'user'
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="owner")
    alerts = relationship("Alert", back_populates="owner")

# ==========================================
# 2. Market Data (Stocks & Financials)
# ==========================================
class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    company_name = Column(String)
    sector = Column(String, index=True) 
    
    fundamentals = relationship("Fundamental", back_populates="stock", uselist=False)
    quarterly_financials = relationship("QuarterlyFinancial", back_populates="stock")
    portfolio_items = relationship("PortfolioItem", back_populates="stock")
    alerts = relationship("Alert", back_populates="stock")

class Fundamental(Base):
    __tablename__ = "fundamentals"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), unique=True, nullable=False)
    
    current_price = Column(Float)
    pe_ratio = Column(Float, index=True)
    peg_ratio = Column(Float, index=True)
    market_cap = Column(Float, index=True)
    debt_to_fcf = Column(Float, index=True)
    promoter_holding = Column(Float)
    revenue_growth_yoy = Column(Float, index=True)
    
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    stock = relationship("Stock", back_populates="fundamentals")

class QuarterlyFinancial(Base):
    __tablename__ = "quarterly_financials"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    
    period_date = Column(Date)
    revenue = Column(Float)
    net_profit = Column(Float)
    ebitda = Column(Float)
    eps = Column(Float)
    
    stock = relationship("Stock", back_populates="quarterly_financials")

    # Composite Index for fast "Last N Quarters" queries
    __table_args__ = (
        Index('idx_stock_period', 'stock_id', period_date.desc()),
    )

# ==========================================
# 3. Portfolio Management
# ==========================================
class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, default="My Portfolio")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="portfolios")
    items = relationship("PortfolioItem", back_populates="portfolio", cascade="all, delete-orphan")

class PortfolioItem(Base):
    __tablename__ = "portfolio_items"
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    
    quantity = Column(Float, default=0.0)
    buy_price = Column(Float, default=0.0)
    buy_date = Column(Date, default=func.current_date())

    portfolio = relationship("Portfolio", back_populates="items")
    stock = relationship("Stock", back_populates="portfolio_items")

# ==========================================
# 4. Alerts System
# ==========================================
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    
    condition_type = Column(String)  # e.g., 'price_above', 'price_below', 'pe_below'
    target_value = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="alerts")
    stock = relationship("Stock", back_populates="alerts")