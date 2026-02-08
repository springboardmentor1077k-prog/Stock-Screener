import os
import sys
import requests
from datetime import datetime
from typing import List, Dict, Any

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import fetch_one, execute_query, get_db_connection

API_KEY = "6D3G16MS0154LRXP"
TARGET_SYMBOLS = ["INFY.BSE", "RELIANCE.BSE", "TCS.BSE", "HDFCBANK.BSE", "ICICIBANK.BSE"]
USD_TO_INR = 91.0

def convert_to_inr(value, currency):
    if not value: return 0.0
    try:
        val = float(value)
        return val * USD_TO_INR if currency == 'USD' else val
    except (ValueError, TypeError): return 0.0

def upsert_stock_data(symbol: str):
    print(f"Fetching Alpha Vantage data for {symbol}...")
    try:
        overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
        data = requests.get(overview_url).json()
        if not data or "Symbol" not in data:
            print(f"  Warning: No overview data found for {symbol}")
            return

        currency = data.get("Currency", "INR")
        market_cap = convert_to_inr(data.get("MarketCapitalization"), currency)
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Upsert Stock
                cur.execute("SELECT id FROM stock WHERE symbol = %s", (symbol,))
                row = cur.fetchone()
                if not row:
                    cur.execute("""
                        INSERT INTO stock (symbol, company_name, sector, industry, exchange, market_cap, listing_date, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (symbol, data.get("Name", symbol), data.get("Sector", "Unknown"), data.get("Industry", "Unknown"), 
                          data.get("Exchange", "BSE"), market_cap, datetime.now().date(), "ACTIVE"))
                    stock_id = cur.fetchone()[0]
                else:
                    stock_id = row[0]
                    cur.execute("""
                        UPDATE stock SET company_name=%s, sector=%s, industry=%s, exchange=%s, market_cap=%s WHERE id=%s
                    """, (data.get("Name"), data.get("Sector"), data.get("Industry"), data.get("Exchange"), market_cap, stock_id))

                # Upsert Fundamentals
                pe_ratio = float(data.get("TrailingPE", 0.0))
                div_yield = float(data.get("DividendYield", 0.0)) * 100
                cur.execute("SELECT id FROM fundamentals WHERE stock_id = %s", (stock_id,))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO fundamentals (stock_id, market_cap, pe_ratio, div_yield, current_price)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (stock_id, market_cap, pe_ratio, div_yield, 0.0))
                else:
                    cur.execute("""
                        UPDATE fundamentals SET market_cap=%s, pe_ratio=%s, div_yield=%s WHERE stock_id=%s
                    """, (market_cap, pe_ratio, div_yield, stock_id))
        print(f"Successfully synced {symbol}")
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")

def main():
    print("Starting data fetch using Alpha Vantage...")
    for symbol in TARGET_SYMBOLS:
        upsert_stock_data(symbol)
    print("Data sync complete.")

if __name__ == "__main__":
    main()
