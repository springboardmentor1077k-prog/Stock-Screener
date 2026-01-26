import yfinance as yf
import time
import pandas as pd
from db import get_db

def safe_int(value, default=0):
    """Safely convert value to int."""
    if pd.isna(value) or value in [None, "None", "N/A", "-", ""]:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def ingest_quarterly():
    """Ingest quarterly financial data for all stocks in database using yfinance."""
    print("Starting quarterly financials ingestion using yfinance...")
    
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT stock_id, symbol FROM stocks ORDER BY stock_id")
    stocks = cur.fetchall()

    if not stocks:
        print("No stocks found in database. Please run ingest_stocks.py first.")
        return

    print(f"Processing quarterly financials for {len(stocks)} stocks...")
    
    successful_updates = 0
    failed_updates = 0
    total_quarters_processed = 0

    for i, stock in enumerate(stocks):
        print(f"\nProcessing quarterly financials for {stock['symbol']} ({i+1}/{len(stocks)})...")
        
        try:
            ticker = yf.Ticker(stock['symbol'])
            
            quarterly_financials = ticker.quarterly_financials
            
            if quarterly_financials is None or quarterly_financials.empty:
                print(f"✗ No quarterly financial data found for {stock['symbol']}")
                failed_updates += 1
                continue

            quarters_inserted = 0
            
            for date, data in quarterly_financials.items():
                try:
                    # Extract date information
                    year = date.year
                    quarter_num = ((date.month - 1) // 3) + 1
                    quarter = f"Q{quarter_num}"
                    
                    revenue = safe_int(data.get('Total Revenue', 0))
                    if revenue == 0:
                        revenue = safe_int(data.get('Revenue', 0))
                    
                    ebitda = safe_int(data.get('EBITDA', 0))
                    if ebitda == 0:
                        operating_income = safe_int(data.get('Operating Income', 0))
                        depreciation = safe_int(data.get('Depreciation', 0))
                        ebitda = operating_income + depreciation
                    
                    net_income = safe_int(data.get('Net Income', 0))
                    if net_income == 0:
                        net_income = safe_int(data.get('Net Income From Continuing Ops', 0))
                    
                    cur.execute("""
                        INSERT IGNORE INTO quarterly_finance
                        (stock_id, quarter, year, revenue, ebitda, net_profit)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (
                        stock["stock_id"],
                        quarter,
                        year,
                        revenue,
                        ebitda,
                        net_income
                    ))
                    
                    quarters_inserted += 1
                    total_quarters_processed += 1
                    
                except Exception as e:
                    print(f"  ⚠️  Error processing quarter {date}: {str(e)}")
                    continue

            if quarters_inserted > 0:
                print(f"✓ Inserted {quarters_inserted} quarters for {stock['symbol']}")
                successful_updates += 1
            else:
                print(f"✗ No quarters inserted for {stock['symbol']}")
                failed_updates += 1
            
            time.sleep(0.5)
                
        except Exception as e:
            print(f"✗ Error processing quarterly financials for {stock['symbol']}: {str(e)}")
            failed_updates += 1
            continue

    db.commit()
    cur.close()
    db.close()
    
    print(f"\n{'='*50}")
    print(f"Quarterly financials ingestion completed!")
    print(f"✓ Successful stocks: {successful_updates}")
    print(f"✗ Failed stocks: {failed_updates}")
    print(f"Total quarters processed: {total_quarters_processed}")
    print(f"Total stocks processed: {len(stocks)}")
    print(f"{'='*50}")

if __name__ == "__main__":
    ingest_quarterly()