import sqlite3
import os
from datetime import date, timedelta
import random

# -------------------------
# ABSOLUTE DB PATH
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "stocks.db")

# -------------------------
# CONNECTION
# -------------------------
def get_connection():
    return sqlite3.connect(DB_PATH)

# -------------------------
# CREATE TABLES
# -------------------------
def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS masterstocks (
        stock_id INTEGER PRIMARY KEY,
        symbol TEXT,
        company_name TEXT,
        sector TEXT,
        industry TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fundamentals (
        stock_id INTEGER,
        pe_ratio REAL,
        market_cap INTEGER,
        profit INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS time_series_financials (
        stock_id INTEGER,
        date TEXT,
        close_price REAL,
        volume INTEGER,
        net_profit INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        query TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alert_triggers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id INTEGER,
        stock_id INTEGER,
        triggered_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# -------------------------
# SEED DATA (25 STOCKS)
# -------------------------
def seed_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM masterstocks")
    cur.execute("DELETE FROM fundamentals")
    cur.execute("DELETE FROM time_series_financials")

    stocks = [
        (1,"TCS","Tata Consultancy Services","IT","SERVICES"),
        (2,"INFY","Infosys","IT","SERVICES"),
        (3,"WIPRO","Wipro","IT","SERVICES"),
        (4,"HCLTECH","HCL Technologies","IT","SERVICES"),
        (5,"TECHM","Tech Mahindra","IT","SERVICES"),
        (6,"HDFC","HDFC Bank","BANK","FINANCE"),
        (7,"ICICIBANK","ICICI Bank","BANK","FINANCE"),
        (8,"SBIN","State Bank of India","BANK","FINANCE"),
        (9,"AXISBANK","Axis Bank","BANK","FINANCE"),
        (10,"KOTAKBANK","Kotak Mahindra Bank","BANK","FINANCE"),
        (11,"RELIANCE","Reliance Industries","ENERGY","OIL"),
        (12,"ONGC","ONGC","ENERGY","OIL"),
        (13,"IOC","Indian Oil","ENERGY","OIL"),
        (14,"HINDUNILVR","HUL","FMCG","CONSUMER"),
        (15,"ITC","ITC Ltd","FMCG","CONSUMER"),
        (16,"NESTLEIND","Nestle India","FMCG","CONSUMER"),
        (17,"SUNPHARMA","Sun Pharma","PHARMA","HEALTH"),
        (18,"DRREDDY","Dr Reddy's","PHARMA","HEALTH"),
        (19,"CIPLA","Cipla","PHARMA","HEALTH"),
        (20,"TATAMOTORS","Tata Motors","AUTO","MANUFACTURING"),
        (21,"M&M","Mahindra & Mahindra","AUTO","MANUFACTURING"),
        (22,"MARUTI","Maruti Suzuki","AUTO","MANUFACTURING"),
        (23,"LT","Larsen & Toubro","INFRA","CONSTRUCTION"),
        (24,"ULTRACEMCO","UltraTech Cement","INFRA","CEMENT"),
        (25,"ADANIENT","Adani Enterprises","INFRA","DIVERSIFIED")
    ]

    cur.executemany(
        "INSERT INTO masterstocks VALUES (?, ?, ?, ?, ?)", stocks
    )

    for s in stocks:
        cur.execute(
            "INSERT INTO fundamentals VALUES (?, ?, ?, ?)",
            (s[0], random.uniform(10, 35), random.randint(50000, 500000), random.randint(5000, 60000))
        )

        for i in range(4):
            d = date.today() - timedelta(days=90 * i)
            cur.execute(
                "INSERT INTO time_series_financials VALUES (?, ?, ?, ?, ?)",
                (s[0], d.isoformat(), random.randint(100, 3500),
                 random.randint(100000, 2000000),
                 random.randint(-5000, 60000))
            )

    conn.commit()
    conn.close()

# -------------------------
# SNAPSHOT SCREENER (FIXED)
# -------------------------
def get_screening_data(where_clause=""):
    conn = get_connection()
    cur = conn.cursor()

    query = f"""
    SELECT
        m.stock_id,                      -- ✅ REQUIRED FOR ALERTS
        m.symbol,
        m.company_name AS company,
        m.sector,
        f.pe_ratio,
        f.market_cap,
        f.profit,
        t.close_price,
        t.volume
    FROM masterstocks m
    JOIN fundamentals f ON m.stock_id = f.stock_id
    JOIN time_series_financials t ON m.stock_id = t.stock_id
    WHERE t.date = (
        SELECT MAX(date)
        FROM time_series_financials
        WHERE stock_id = m.stock_id
    )
    {where_clause}
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    cols = [
        "stock_id",      # ✅ THIS FIXES THE ERROR
        "symbol",
        "company",
        "sector",
        "pe_ratio",
        "market_cap",
        "profit",
        "close_price",
        "volume"
    ]

    return [dict(zip(cols, r)) for r in rows]

# -------------------------
# INIT
# -------------------------
if __name__ == "__main__":
    create_tables()
    seed_data()
    print("DB READY (alerts-safe):", DB_PATH)
