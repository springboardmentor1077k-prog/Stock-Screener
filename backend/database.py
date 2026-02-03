import sqlite3
import os
from datetime import date, timedelta
import random

# -------------------------
# DATABASE PATH
# -------------------------
DB_PATH = os.path.join("..", "data", "stocks.db")


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
        symbol TEXT UNIQUE,
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
        profit INTEGER,
        FOREIGN KEY (stock_id) REFERENCES masterstocks(stock_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS time_series_financials (
        stock_id INTEGER,
        date TEXT,
        close_price REAL,
        volume INTEGER,
        net_profit INTEGER,
        FOREIGN KEY (stock_id) REFERENCES masterstocks(stock_id)
    )
    """)

    # -------- INDEXES --------
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_timeseries_stock_date
    ON time_series_financials (stock_id, date)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_fundamentals_stock
    ON fundamentals (stock_id)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_masterstocks_symbol
    ON masterstocks (symbol)
    """)

    conn.commit()
    conn.close()


# -------------------------
# SEED DATA (25 COMPANIES)
# -------------------------
def seed_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM masterstocks")
    cur.execute("DELETE FROM fundamentals")
    cur.execute("DELETE FROM time_series_financials")

    # ---------- 25 COMPANIES ----------
    stocks = [
        (1, "TCS", "Tata Consultancy Services", "IT", "SERVICES"),
        (2, "INFY", "Infosys", "IT", "SERVICES"),
        (3, "WIPRO", "Wipro Ltd", "IT", "SERVICES"),
        (4, "HCLTECH", "HCL Technologies", "IT", "SERVICES"),
        (5, "TECHM", "Tech Mahindra", "IT", "SERVICES"),

        (6, "HDFC", "HDFC Bank", "BANK", "FINANCE"),
        (7, "ICICIBANK", "ICICI Bank", "BANK", "FINANCE"),
        (8, "SBIN", "State Bank of India", "BANK", "FINANCE"),
        (9, "AXISBANK", "Axis Bank", "BANK", "FINANCE"),
        (10, "KOTAKBANK", "Kotak Mahindra Bank", "BANK", "FINANCE"),

        (11, "RELIANCE", "Reliance Industries", "ENERGY", "OIL & GAS"),
        (12, "ONGC", "Oil and Natural Gas Corp", "ENERGY", "OIL & GAS"),
        (13, "IOC", "Indian Oil Corp", "ENERGY", "OIL & GAS"),

        (14, "HINDUNILVR", "Hindustan Unilever", "FMCG", "CONSUMER"),
        (15, "ITC", "ITC Ltd", "FMCG", "CONSUMER"),
        (16, "NESTLEIND", "Nestle India", "FMCG", "CONSUMER"),

        (17, "SUNPHARMA", "Sun Pharma", "PHARMA", "HEALTHCARE"),
        (18, "DRREDDY", "Dr Reddy’s Labs", "PHARMA", "HEALTHCARE"),
        (19, "CIPLA", "Cipla Ltd", "PHARMA", "HEALTHCARE"),

        (20, "TATAMOTORS", "Tata Motors", "AUTO", "MANUFACTURING"),
        (21, "M&M", "Mahindra & Mahindra", "AUTO", "MANUFACTURING"),
        (22, "MARUTI", "Maruti Suzuki", "AUTO", "MANUFACTURING"),

        (23, "LT", "Larsen & Toubro", "INFRA", "CONSTRUCTION"),
        (24, "ULTRACEMCO", "UltraTech Cement", "INFRA", "CEMENT"),
        (25, "ADANIENT", "Adani Enterprises", "INFRA", "DIVERSIFIED"),
    ]

    cur.executemany("""
        INSERT INTO masterstocks
        (stock_id, symbol, company_name, sector, industry)
        VALUES (?, ?, ?, ?, ?)
    """, stocks)

    # ---------- FUNDAMENTALS ----------
    fundamentals = []
    for stock in stocks:
        stock_id = stock[0]
        fundamentals.append((
            stock_id,
            round(random.uniform(10, 30), 2),       # PE
            random.randint(50000, 500000),          # Market Cap
            random.randint(5000, 60000)              # Profit
        ))

    cur.executemany("""
        INSERT INTO fundamentals
        (stock_id, pe_ratio, market_cap, profit)
        VALUES (?, ?, ?, ?)
    """, fundamentals)

    # ---------- TIME SERIES (4 QUARTERS EACH) ----------
    today = date.today()

    for stock_id in range(1, 26):
        for i in range(4):
            d = today - timedelta(days=90 * i)
            cur.execute("""
                INSERT INTO time_series_financials
                (stock_id, date, close_price, volume, net_profit)
                VALUES (?, ?, ?, ?, ?)
            """, (
                stock_id,
                d.isoformat(),
                random.randint(100, 3500),
                random.randint(100000, 2000000),
                random.randint(-5000, 60000)
            ))

    conn.commit()
    conn.close()


# -------------------------
# SNAPSHOT SCREENER QUERY
# -------------------------
def get_screening_data(where_clause=""):
    conn = get_connection()
    cur = conn.cursor()

    query = f"""
    SELECT
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
        "symbol", "company", "sector",
        "pe_ratio", "market_cap", "profit",
        "close_price", "volume"
    ]

    return [dict(zip(cols, r)) for r in rows]


# -------------------------
# RUN ONCE
# -------------------------
if __name__ == "__main__":
    create_tables()
    seed_data()
    print("✅ Database created with 25 companies")

