import yfinance as yf
import time
from db import get_db

def safe_float(value, default=0.0):
    """Safely convert value to float."""
    if value in [None, "None", "N/A", "-", ""]:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to int."""
    if value in [None, "None", "N/A", "-", ""]:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def ingest_fundamentals():
    """Ingest fundamental data for all stocks in database using yfinance."""
    print("Starting fundamentals ingestion using yfinance...")
    
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT stock_id, symbol FROM stocks ORDER BY stock_id")
    stocks = cur.fetchall()

    if not stocks:
        print("No stocks found in database. Please run ingest_stocks.py first.")
        return

    print(f"Processing fundamentals for {len(stocks)} stocks...")
    
    successful_updates = 0
    failed_updates = 0

    for i, stock in enumerate(stocks):
        print(f"\nProcessing fundamentals for {stock['symbol']} ({i+1}/{len(stocks)})...")
        
        try:
            ticker = yf.Ticker(stock['symbol'])
            info = ticker.info
            
            if not info:
                print(f"✗ No data found for {stock['symbol']}")
                failed_updates += 1
                continue

            pe_ratio = safe_float(info.get('trailingPE') or info.get('forwardPE'))
            eps = safe_float(info.get('trailingEps') or info.get('forwardEps'))
            market_cap = safe_int(info.get('marketCap'))
            roe = safe_float(info.get('returnOnEquity'))
            debt_equity = safe_float(info.get('debtToEquity'))
            
            book_value = safe_float(info.get('bookValue'))
            dividend_yield = safe_float(info.get('dividendYield'))
            profit_margin = safe_float(info.get('profitMargins'))
            operating_margin = safe_float(info.get('operatingMargins'))
            revenue_growth = safe_float(info.get('revenueGrowth'))
            
            cur.execute("""
                INSERT INTO fundamentals
                (stock_id, pe_ratio, eps, market_cap, roe, debt_equity, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,NOW())
                ON DUPLICATE KEY UPDATE
                    pe_ratio=VALUES(pe_ratio),
                    eps=VALUES(eps),
                    market_cap=VALUES(market_cap),
                    roe=VALUES(roe),
                    debt_equity=VALUES(debt_equity),
                    updated_at=NOW()
            """, (
                stock["stock_id"],
                pe_ratio,
                eps,
                market_cap,
                roe,
                debt_equity,
            ))

            print(f"✓ Updated: {stock['symbol']} (PE: {pe_ratio}, EPS: {eps}, Market Cap: {market_cap:,})")
            successful_updates += 1
            
            time.sleep(0.5)
                
        except Exception as e:
            print(f"✗ Error processing fundamentals for {stock['symbol']}: {str(e)}")
            failed_updates += 1
            continue

    db.commit()
    cur.close()
    db.close()
    
    print(f"\n{'='*50}")
    print(f"Fundamentals ingestion completed!")
    print(f"✓ Successful: {successful_updates}")
    print(f"✗ Failed: {failed_updates}")
    print(f"Total processed: {len(stocks)}")
    print(f"{'='*50}")

if __name__ == "__main__":
    ingest_fundamentals()