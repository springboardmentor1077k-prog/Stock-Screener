import psycopg2
import random
import requests

# Config
DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}
API_URL = "http://localhost:8000"

# We will create rules that are GUARANTEED to trigger
# e.g., If Apple is $220, we create a rule "Apple > $150"
def seed_smart_alerts():
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cur = conn.cursor()
    print("🚀 Seeding Smart Alerts...")

    try:
        # 1. Get the first user
        cur.execute("SELECT user_id, email FROM users LIMIT 1")
        user = cur.fetchone()
        
        if not user:
            print("❌ No users found! Please signup/login first.")
            return

        user_id, email = user
        print(f"👤 Creating alerts for: {email}")

        # 2. Get some real stocks with prices from your DB
        cur.execute("""
            SELECT s.ticker, a.current_price, f.pe_ratio 
            FROM stocks s
            JOIN analysis_target a ON s.stock_id = a.stock_id
            LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
            WHERE a.current_price IS NOT NULL
            LIMIT 5
        """)
        stocks = cur.fetchall()

        if not stocks:
            print("❌ No stock data found! Run 'fetch_yfinance.py' first.")
            return

        # 3. Clear old alerts to avoid duplicates
        cur.execute("DELETE FROM alerts WHERE user_id = %s", (user_id,))
        
        count = 0
        for ticker, price, pe in stocks:
            price = float(price)
            
            # --- Rule 1: Price Alert (Guaranteed Trigger) ---
            # Set threshold slightly BELOW current price so it triggers "Price > X"
            threshold_price = round(price * 0.9, 2) 
            
            cur.execute("""
                INSERT INTO alerts (user_id, metric, operator, threshold)
                VALUES (%s, 'price', '>', %s)
            """, (user_id, threshold_price))
            print(f"   ✅ Added Rule: Alert if {ticker} Price > ${threshold_price} (Current: ${price})")
            count += 1

            # --- Rule 2: PE Ratio Alert (Random) ---
            if pe and pe > 0:
                # Set threshold slightly ABOVE current PE so it triggers "PE < X"
                threshold_pe = float(pe) + 5.0
                cur.execute("""
                    INSERT INTO alerts (user_id, metric, operator, threshold)
                    VALUES (%s, 'pe_ratio', '<', %s)
                """, (user_id, threshold_pe))
                print(f"   ✅ Added Rule: Alert if {ticker} PE < {threshold_pe:.2f} (Current: {pe})")
                count += 1

        conn.commit()
        print(f"\n🎉 Created {count} Active Rules.")
        print("   Now go to the Dashboard -> Alerts Tab -> Click '⚡ Run Check Now'")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_smart_alerts()
