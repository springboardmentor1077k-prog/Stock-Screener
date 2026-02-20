import psycopg2
import zlib

DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

# Realistic Mock Data (Ticker: Current, High Target, Low Target)
MOCK_DATA = {
    "AAPL": {"current": 225.50, "high": 260.00, "low": 180.00},
    "MSFT": {"current": 415.00, "high": 480.00, "low": 400.00},
    "NVDA": {"current": 120.00, "high": 150.00, "low": 110.00},
    "TSLA": {"current": 240.00, "high": 310.00, "low": 160.00},
    "GOOGL": {"current": 175.00, "high": 200.00, "low": 165.00},
    "AMD":   {"current": 160.00, "high": 190.00, "low": 140.00},
    "XOM": {"current": 115.00, "high": 135.00, "low": 105.00}
}

def populate_targets():
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cur = conn.cursor()
    print("🚀 Populating Analysis Targets...")

    try:
        # Clear old data to avoid duplicates
        cur.execute("TRUNCATE TABLE analysis_target")
        
        for ticker, data in MOCK_DATA.items():
            # 1. Get the correct Stock ID from your stocks table
            cur.execute("SELECT stock_id FROM stocks WHERE ticker = %s", (ticker,))
            result = cur.fetchone()
            
            if result:
                stock_id = result[0]
                
                # 2. Insert Mock Analyst Data
                cur.execute("""
                    INSERT INTO analysis_target (stock_id, current_price, high_target_price, low_target_price)
                    VALUES (%s, %s, %s, %s)
                """, (stock_id, data['current'], data['high'], data['low']))
                
                print(f"   ✅ Added targets for {ticker} (ID: {stock_id})")
            else:
                print(f"   ⚠️ Skipped {ticker} (Not found in stocks table)")

        conn.commit()
        print("\n🎉 Analyst data populated successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    populate_targets()