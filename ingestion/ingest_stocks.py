import yfinance as yf
import time
from db import get_db

SYMBOLS = [
    "AAPL",    # Apple Inc.
    "MSFT",    # Microsoft Corporation
    "GOOGL",   # Alphabet Inc.
    "AMZN",    # Amazon.com Inc.
    "TSLA",    # Tesla Inc.
    "META",    # Meta Platforms Inc.
    "NVDA",    # NVIDIA Corporation
    "NFLX",    # Netflix Inc.
    "ADBE",    # Adobe Inc.
    "CRM",     # Salesforce Inc.
    "JPM",     # JPMorgan Chase & Co.
    "V",       # Visa Inc.
    "MA",      # Mastercard Inc.
    "BAC",     # Bank of America Corp.
    "WMT",     # Walmart Inc.
    "JNJ",     # Johnson & Johnson
    "PG",      # Procter & Gamble Co.
    "UNH",     # UnitedHealth Group Inc.
    "HD",      # The Home Depot Inc.
    "DIS",     # The Walt Disney Company
    "XOM",     # Exxon Mobil Corporation
    "KO",      # The Coca-Cola Company
    "PFE",     # Pfizer Inc.
    "INTC",    # Intel Corporation
    "CSCO",    # Cisco Systems Inc.
    
    "INFY",    # Infosys Ltd. (NASDAQ ADR)
    "WIT",     # Wipro Ltd. (NYSE ADR)
    "HDB",     # HDFC Bank Ltd. (NYSE ADR)
    "IBN",     # ICICI Bank Ltd. (NYSE ADR)
    "TTM",     # Tata Motors Ltd. (NYSE ADR)
]

def test_yfinance_connection():
    """Test yfinance connection with a sample request."""
    print("Testing yfinance connection...")
    
    try:
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        if info and 'symbol' in info:
            print(f"✓ yfinance connection successful. Sample data for AAPL:")
            print(f"  Company: {info.get('longName', 'N/A')}")
            print(f"  Sector: {info.get('sector', 'N/A')}")
            print(f"  Industry: {info.get('industry', 'N/A')}")
            print(f"  Market Cap: {info.get('marketCap', 'N/A')}")
            return True
        else:
            print(f"✗ yfinance connection failed. Response: {info}")
            return False
            
    except Exception as e:
        print(f"✗ yfinance connection error: {str(e)}")
        return False

def ingest_stocks():
    """Ingest stock information using yfinance."""
    print(f"Starting stock ingestion for {len(SYMBOLS)} companies using yfinance...")
    
    if not test_yfinance_connection():
        print("Aborting ingestion due to yfinance connection issues.")
        return
    
    db = get_db()
    cur = db.cursor()
    
    successful_inserts = 0
    failed_inserts = 0

    for i, symbol in enumerate(SYMBOLS):
        print(f"\nProcessing {symbol} ({i+1}/{len(SYMBOLS)})...")
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                print(f"✗ No data found for {symbol}")
                failed_inserts += 1
                continue

            company_name = info.get('longName', info.get('shortName', ''))
            sector = info.get('sector', '')
            industry = info.get('industry', '')
            exchange = info.get('exchange', 'NASDAQ')
            
            if symbol in ["INFY", "WIT", "HDB", "IBN", "TTM"]:
                exchange = "NYSE/NASDAQ (Indian ADR)"
            
            cur.execute("""
                INSERT IGNORE INTO stocks (symbol, company_name, sector, industry, exchange, isin)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                symbol,
                company_name[:100] if company_name else '',
                sector[:50] if sector else '',
                industry[:50] if industry else '',
                exchange[:20] if exchange else '',
                ''
            ))

            print(f"✓ Inserted: {symbol} - {company_name}")
            successful_inserts += 1
            
            time.sleep(0.5)
                
        except Exception as e:
            print(f"✗ Error processing {symbol}: {str(e)}")
            failed_inserts += 1
            continue

    db.commit()
    cur.close()
    db.close()
    
    print(f"\n{'='*50}")
    print(f"Stock ingestion completed!")
    print(f"✓ Successful: {successful_inserts}")
    print(f"✗ Failed: {failed_inserts}")
    print(f"Total processed: {len(SYMBOLS)}")
    print(f"{'='*50}")

if __name__ == "__main__":
    ingest_stocks()