import yfinance as yf
import logging
import random
from datetime import date, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .database import SessionLocal
from .models import Stock, Fundamental, QuarterlyFinancial, User, Portfolio, PortfolioItem, Alert

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Password Hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# List of 15 Major Indian Stocks to Seed
TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "BAJFINANCE.NS",
    "TATAMOTORS.NS", "MARUTI.NS", "SUNPHARMA.NS", "ASIANPAINT.NS", "HCLTECH.NS"
]

def seed():
    db = SessionLocal()
    try:
        # 1. Check if stocks already exist
        if db.query(Stock).count() > 0:
            logger.warning("Stocks already exist in DB. Skipping stock seed.")
        else:
            logger.info(f"🌍 Fetching live data for {len(TICKERS)} stocks...")
            
            for symbol in TICKERS:
                try:
                    logger.info(f"   -> Processing {symbol}...")
                    ticker = yf.Ticker(symbol)
                    
                    fast = getattr(ticker, "fast_info", {})
                    info = ticker.info or {}

                    price = fast.get("last_price") or info.get("currentPrice") or 0.0
                    mcap = fast.get("market_cap") or info.get("marketCap") or 0.0
                    pe = info.get("trailingPE", 0.0)
                    rev_growth = info.get("revenueGrowth", 0.0)
                    promoter = info.get("heldPercentInsiders", 0.0) * 100

                    if pe > 0 and rev_growth > 0:
                        peg = round(pe / (rev_growth * 100), 2)
                    else:
                        peg = info.get("pegRatio", 0.0)

                    clean_symbol = symbol.replace(".NS", "")
                    stock = Stock(
                        symbol=clean_symbol, 
                        company_name=info.get('shortName', symbol), 
                        sector=info.get('sector', 'Unknown')
                    )
                    db.add(stock)
                    db.flush() 

                    db.add(Fundamental(
                        stock_id=stock.id, 
                        current_price=price, 
                        pe_ratio=pe, 
                        peg_ratio=peg,
                        market_cap=mcap, 
                        debt_to_fcf=0.0,
                        promoter_holding=promoter,
                        revenue_growth_yoy=rev_growth
                    ))

                    for i in range(4):
                        base = mcap / 50 
                        factor = 1.0 - (i * 0.02)
                        db.add(QuarterlyFinancial(
                            stock_id=stock.id, 
                            period_date=date.today() - timedelta(days=90*i),
                            revenue=base * factor, 
                            net_profit=base * 0.15 * factor,
                            ebitda=base * 0.18, 
                            eps=10.0
                        ))

                except Exception as e:
                    logger.error(f"Failed to fetch {symbol}: {e}")

            db.commit()
            logger.info("Stocks seeded successfully!")

        # 2. Seed Clean Admin User
        if not db.query(User).filter_by(username="admin").first():
            logger.info("Creating Admin User...")
            
            # Securely hash the password 'admin123'
            hashed_pw = pwd_context.hash("admin123")
            
            admin = User(username="admin", hashed_password=hashed_pw, role="admin")
            db.add(admin)
            
            # Create an empty default portfolio for the admin
            portfolio = Portfolio(user_id=admin.id, name="My Portfolio")
            db.add(portfolio)
            
            db.commit()
            logger.info("Admin user created successfully! (Password: admin123)")

    except Exception as e:
        db.rollback()
        logger.error(f"Critical Seed Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
