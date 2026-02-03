import psycopg2
import random

DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

# Expanded list of stocks
TARGET_TICKERS = [
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMD', 
    'TSLA', 'AMZN', 'META', 'NFLX', 'INTC', 
    'CSCO', 'ORCL', 'IBM', 'QCOM', 'TXN',
    'ADBE', 'CRM', 'AVGO', 'PYPL', 'UBER'
]

def seed_portfolio():
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cur = conn.cursor()
    print("🚀 Seeding Portfolio Data...")

    try:
        # 1. Get ALL users (Removed LIMIT 1)
        cur.execute("SELECT user_id, email FROM users")
        users = cur.fetchall()
        
        if not users:
            print("❌ No users found! Please signup a user via the UI first.")
            return

        print(f"👥 Found {len(users)} users. Updating portfolios...")

        for user_id, email in users:
            print(f"   👤 Processing user: {email} (ID: {user_id})")

            # Clear old portfolio for this user
            cur.execute("DELETE FROM portfolio WHERE user_id = %s", (user_id,))
            
            count = 0
            for ticker in TARGET_TICKERS:
                cur.execute("SELECT stock_id FROM stocks WHERE ticker = %s", (ticker,))
                res = cur.fetchone()
                
                if res:
                    stock_id = res[0]
                    # 50% chance to own this stock
                    if random.random() > 0.5: 
                        qty = random.randint(10, 100)
                        avg_price = random.uniform(50.0, 450.0) 
                        
                        cur.execute("""
                            INSERT INTO portfolio (user_id, stock_id, quantity, average_price)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, stock_id, qty, avg_price))
                        count += 1

            print(f"      ✅ Added {count} positions.")

        conn.commit()
        print(f"\n🎉 Successfully updated portfolios for all {len(users)} users!")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_portfolio()
