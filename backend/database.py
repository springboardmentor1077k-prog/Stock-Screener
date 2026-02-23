import sqlite3
import os
import random
from datetime import date, timedelta, datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "stocks.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

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
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        portfolio_id INTEGER,
        stock_id INTEGER,
        quantity INTEGER,
        buy_price REAL,
        buy_time TEXT
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
        triggered_at TEXT,
        UNIQUE(alert_id, stock_id)
    )
    """)

    conn.commit()
    conn.close()

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
        (10,"KOTAKBANK","Kotak Bank","BANK","FINANCE"),
        (11,"RELIANCE","Reliance Industries","ENERGY","OIL"),
        (12,"ONGC","ONGC","ENERGY","OIL"),
        (13,"IOC","Indian Oil","ENERGY","OIL"),
        (14,"ITC","ITC Ltd","FMCG","CONSUMER"),
        (15,"HINDUNILVR","HUL","FMCG","CONSUMER"),
        (16,"NESTLEIND","Nestle","FMCG","CONSUMER"),
        (17,"SUNPHARMA","Sun Pharma","PHARMA","HEALTH"),
        (18,"DRREDDY","Dr Reddy","PHARMA","HEALTH"),
        (19,"CIPLA","Cipla","PHARMA","HEALTH"),
        (20,"TATAMOTORS","Tata Motors","AUTO","MANUFACTURING"),
        (21,"M&M","Mahindra","AUTO","MANUFACTURING"),
        (22,"MARUTI","Maruti","AUTO","MANUFACTURING"),
        (23,"LT","L&T","INFRA","CONSTRUCTION"),
        (24,"ULTRACEMCO","UltraTech","INFRA","CEMENT"),
        (25,"ADANIENT","Adani Ent","INFRA","DIVERSIFIED"),
    ]

    cur.executemany("INSERT INTO masterstocks VALUES (?,?,?,?,?)", stocks)

    fundamentals = [
        (s[0], round(random.uniform(12,25),2),
         random.randint(50000,500000),
         random.randint(1000,60000))
        for s in stocks
    ]
    cur.executemany("INSERT INTO fundamentals VALUES (?,?,?,?)", fundamentals)

    today = date.today()

    for sid in range(1,26):
        for q in range(4):
            cur.execute("""
            INSERT INTO time_series_financials
            VALUES (?,?,?,?,?)
            """, (
                sid,
                (today - timedelta(days=90*q)).isoformat(),
                random.randint(500,3500),
                random.randint(100000,2000000),
                random.randint(-5000,60000)
            ))

    conn.commit()
    conn.close()

def ensure_quarter_rows():
    conn = get_connection()
    cur = conn.cursor()
    today = date.today()

    for sid in range(1,26):
        cur.execute("""
        SELECT COUNT(*)
        FROM time_series_financials
        WHERE stock_id = ?
        """, (sid,))
        count = cur.fetchone()[0]

        if count < 4:
            missing = 4 - count
            for q in range(missing):
                cur.execute("""
                INSERT INTO time_series_financials
                VALUES (?,?,?,?,?)
                """, (
                    sid,
                    (today - timedelta(days=90*q)).isoformat(),
                    random.randint(500,3500),
                    random.randint(100000,2000000),
                    random.randint(-5000,60000)
                ))

    conn.commit()
    conn.close()

def get_screening_data(where_clause=""):
    conn = get_connection()
    cur = conn.cursor()

    query = f"""
    SELECT
        m.stock_id,
        m.symbol,
        m.company_name AS company,
        m.sector,
        f.pe_ratio,
        f.market_cap,
        f.profit,
        t.close_price
    FROM masterstocks m
    JOIN fundamentals f ON m.stock_id = f.stock_id
    JOIN (
        SELECT stock_id, close_price
        FROM time_series_financials
        WHERE (stock_id, date) IN (
            SELECT stock_id, MAX(date)
            FROM time_series_financials
            GROUP BY stock_id
        )
    ) t ON m.stock_id = t.stock_id
    {where_clause}
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    cols = ["stock_id","symbol","company","sector","pe_ratio","market_cap","profit","close_price"]
    return [dict(zip(cols, r)) for r in rows]

def get_portfolio_holdings(portfolio_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        ph.id,
        ph.stock_id,
        m.symbol,
        m.company_name,
        ph.quantity,
        ph.buy_price,
        ph.buy_time,
        t.close_price
    FROM portfolio_holdings ph
    JOIN masterstocks m ON ph.stock_id = m.stock_id
    JOIN time_series_financials t
      ON t.stock_id = ph.stock_id
     AND t.date = (
         SELECT MAX(date)
         FROM time_series_financials
         WHERE stock_id = ph.stock_id
     )
    WHERE ph.portfolio_id = ?
    """, (portfolio_id,))

    rows = cur.fetchall()
    conn.close()

    holdings = []
    for r in rows:
        hid, sid, sym, comp, qty, buy, buy_time, curr = r
        holdings.append({
            "holding_id": hid,
            "stock_id": sid,
            "symbol": sym,
            "company": comp,
            "quantity": qty,
            "buy_price": buy,
            "buy_time": buy_time,
            "current_price": curr
        })

    return holdings

def sell_holding(holding_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM portfolio_holdings WHERE id = ?", (holding_id,))
    conn.commit()
    conn.close()

def simulate_market_prices():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT stock_id, close_price
    FROM time_series_financials
    WHERE (stock_id, date) IN (
        SELECT stock_id, MAX(date)
        FROM time_series_financials
        GROUP BY stock_id
    )
    """)

    rows = cur.fetchall()
    now = datetime.now().isoformat()

    for sid, price in rows:
        new_price = round(price * (1 + random.uniform(-0.05, 0.05)), 2)
        cur.execute("""
        INSERT INTO time_series_financials
        VALUES (?,?,?,?,?)
        """, (
            sid,
            now,
            new_price,
            random.randint(100000,2000000),
            random.randint(-5000,60000)
        ))

    cur.execute("SELECT stock_id, pe_ratio FROM fundamentals")
    for sid, pe in cur.fetchall():
        new_pe = max(1, round(pe * (1 + random.uniform(-0.15,0.15)), 2))
        cur.execute("UPDATE fundamentals SET pe_ratio = ? WHERE stock_id = ?", (new_pe, sid))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    seed_data()
    ensure_quarter_rows()
    print("Database initialized")
