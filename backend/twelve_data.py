import requests
import sqlite3
import os
import time

# -------------------------
# CONFIG
# -------------------------
API_KEY = "2c8bcc267e104870a6aa8a61fd589ca8 "
BASE_URL = "https://api.twelvedata.com"

DB_PATH = os.path.join("..", "data", "stocks.db")

# 10 demo symbols (safe for API limits)
SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "META", "NVDA",
    "TSLA", "AMZN", "IBM", "ORCL", "INTC"
]


# -------------------------
# DB CONNECTION
# -------------------------
def get_connection():
    return sqlite3.connect(DB_PATH)


# -------------------------
# API CALL
# -------------------------
def get_latest_price(symbol):
    params = {
        "symbol": symbol,
        "interval": "1day",
        "apikey": API_KEY,
        "outputsize": 1
    }
    url = f"{BASE_URL}/time_series"
    return requests.get(url, params=params).json()


# -------------------------
# LOADER
# -------------------------
def load_market_data():
    conn = get_connection()
    cur = conn.cursor()

    for idx, symbol in enumerate(SYMBOLS, start=500):
        print(f"📥 Fetching {symbol}")

        data = get_latest_price(symbol)

        # Safety check
        if "values" not in data:
            print(f"⚠️ Skipping {symbol} (API limit or invalid)")
            continue

        latest = data["values"][0]

        # -------------------------
        # Insert masterstocks
        # -------------------------
        cur.execute("""
            INSERT OR IGNORE INTO masterstocks
            (stock_id, symbol, company_name, sector, industry)
            VALUES (?, ?, ?, ?, ?)
        """, (
            idx,
            symbol,
            symbol,
            "TECH",
            "GENERAL"
        ))

        # -------------------------
        # Insert fundamentals (demo values)
        # -------------------------
        cur.execute("""
            INSERT OR IGNORE INTO fundamentals
            (stock_id, pe_ratio, eps, market_cap, revenue, profit)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            idx,
            18.5,
            12.3,
            150000,
            250000,
            60000
        ))

        # -------------------------
        # Insert time series
        # -------------------------
        cur.execute("""
            INSERT INTO time_series_financials
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            idx,
            latest["datetime"],
            float(latest["open"]),
            float(latest["close"]),
            int(float(latest["volume"])),
            12000
        ))

        conn.commit()
        time.sleep(2)   # avoid API rate limit

        print(f"✅ {symbol} inserted")

    conn.close()
    print("\n🎉 Twelve Data loading complete!")


# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    load_market_data()
