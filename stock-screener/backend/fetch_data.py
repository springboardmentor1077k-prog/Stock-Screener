
import os
import sys
import requests
from datetime import datetime
from typing import List, Dict, Any

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.stock import Stock
from app.models.fundamentals import Fundamentals
from app.models.financials import Financials

API_KEY = "6D3G16MS0154LRXP"
# List of major Indian stocks (Nifty 50 tokens for Alpha Vantage)
TARGET_SYMBOLS = ["INFY.BSE", "RELIANCE.BSE", "TCS.BSE", "HDFCBANK.BSE", "ICICIBANK.BSE"]

# Fixed conversion rate for simplicity (1 USD to INR)
USD_TO_INR = 91.0

def convert_to_inr(value, currency):
    if not value:
        return 0.0
    try:
        val = float(value)
        if currency == 'USD':
            return val * USD_TO_INR
        return val
    except (ValueError, TypeError):
        return 0.0

def upsert_stock_data(db: Session, symbol: str):
    print(f"Fetching Alpha Vantage data for {symbol}...")
    try:
        # 1. Fetch OVERVIEW
        overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
        overview_res = requests.get(overview_url)
        data = overview_res.json() if overview_res.status_code == 200 else {}

        if not data or "Symbol" not in data:
            print(f"  Warning: No overview data found for {symbol}")
            return

        currency = data.get("Currency", "INR")
        
        # --- 1. Stocks Table ---
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            print(f"Creating Stock: {symbol}")
            stock = Stock(
                symbol=symbol,
                company_name=data.get("Name", symbol),
                sector=data.get("Sector", "Unknown"),
                industry=data.get("Industry", "Unknown"),
                exchange=data.get("Exchange", "BSE"),
                market_cap=convert_to_inr(data.get("MarketCapitalization"), currency),
                listing_date=datetime.now().date(), # Placeholder if not in OVERVIEW
                status="ACTIVE"
            )
            db.add(stock)
            db.flush()
        else:
            stock.company_name = data.get("Name", stock.company_name)
            stock.sector = data.get("Sector", stock.sector)
            stock.industry = data.get("Industry", stock.industry)
            stock.exchange = data.get("Exchange", stock.exchange)
            stock.market_cap = convert_to_inr(data.get("MarketCapitalization"), currency)

        # --- 2. Fundamentals Table ---
        fundamentals = db.query(Fundamentals).filter(Fundamentals.stock_id == stock.id).first()
        
        pe_ratio = float(data.get("TrailingPE", 0.0))
        div_yield = float(data.get("DividendYield", 0.0)) * 100
        
        # Alpha Vantage OVERVIEW doesn't have real-time price. 
        # We'd need GLOBAL_QUOTE for that, but let's sync what's available.
        if not fundamentals:
            fundamentals = Fundamentals(
                stock_id=stock.id,
                market_cap=stock.market_cap,
                pe_ratio=pe_ratio,
                div_yield=div_yield,
                current_price=0.0 # Will be updated via real-time fetch
            )
            db.add(fundamentals)
        else:
            fundamentals.market_cap = stock.market_cap
            fundamentals.pe_ratio = pe_ratio
            fundamentals.div_yield = div_yield

        # --- 3. Financials Table ---
        # Note: Alpha Vantage has function=INCOME_STATEMENT for full financials
        
        db.commit()
        print(f"Successfully synced {symbol}")

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        db.rollback()

def main():
    print("Starting data fetch using Alpha Vantage...")
    db = SessionLocal()
    try:
        for symbol in TARGET_SYMBOLS:
            upsert_stock_data(db, symbol)
    finally:
        db.close()
    print("Data sync complete.")

if __name__ == "__main__":
    main()
