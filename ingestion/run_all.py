import sys
import time
from datetime import datetime

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_step(step_num, title):
    """Print a formatted step."""
    print(f"\n[STEP {step_num}] {title}")
    print("-" * 40)

def check_yfinance():
    """Check if yfinance is installed and working."""
    try:
        import yfinance as yf
        print("✓ yfinance is installed and ready")
        
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        if info and 'symbol' in info:
            print("✓ yfinance connection test successful")
            return True
        else:
            print("✗ yfinance connection test failed")
            return False
            
    except ImportError:
        print("✗ yfinance is not installed. Please install it with:")
        print("  pip install yfinance")
        return False
    except Exception as e:
        print(f"✗ yfinance test error: {str(e)}")
        return False

def main():
    """Run complete data ingestion pipeline using yfinance."""
    start_time = datetime.now()
    
    print_header("STOCK SCREENER DATA INGESTION PIPELINE (yfinance)")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not check_yfinance():
        print("\nPlease install yfinance and try again:")
        print("  pip install yfinance")
        sys.exit(1)
    
    try:
        print_step(1, "Ingesting Stock Information")
        from ingest_stocks import ingest_stocks
        ingest_stocks()
        
        print("\nWaiting 5 seconds before next step...")
        time.sleep(5)
        
        print_step(2, "Ingesting Fundamental Data")
        from ingest_fundamentals import ingest_fundamentals
        ingest_fundamentals()
        
        print("\nWaiting 5 seconds before next step...")
        time.sleep(5)
        
        print_step(3, "Ingesting Quarterly Financial Data")
        from ingest_quarterly_financials import ingest_quarterly
        ingest_quarterly()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print_header("INGESTION PIPELINE COMPLETED")
        print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration}")
        print("\n✅ All data ingestion completed successfully!")
        print("\nYour stock screener database is now populated with:")
        print("  • Stock information (30 companies from US and Indian markets)")
        print("  • Fundamental metrics (PE ratios, EPS, market cap, ROE, etc.)")
        print("  • Historical quarterly financial data")
        print("  • Real-time data from yfinance (no API limits!)")
        
        print("\n🚀 You can now use your AI stock screener with rich data!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Ingestion interrupted by user (Ctrl+C)")
        print("You can resume by running individual scripts:")
        print("  python ingest_stocks.py")
        print("  python ingest_fundamentals.py")
        print("  python ingest_quarterly_financials.py")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n\n❌ Error during ingestion: {str(e)}")
        print("Check the error above and try running individual scripts:")
        print("  python ingest_stocks.py")
        print("  python ingest_fundamentals.py")
        print("  python ingest_quarterly_financials.py")
        sys.exit(1)

if __name__ == "__main__":
    main()