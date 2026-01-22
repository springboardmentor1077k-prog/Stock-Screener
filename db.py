import psycopg2

# ===============================
# CONFIGURATION
# ===============================

ADMIN_DB_CONFIG = {
    "dbname": "postgres",   # default admin DB
    "user": "postgres",
    "password": "Nethra@02",
    "host": "localhost",
    "port": 5432
}

APP_DB_NAME = "stocks_db"

APP_DB_CONFIG = {
    "dbname": APP_DB_NAME,
    "user": "postgres",
    "password": "Nethra@02",
    "host": "localhost",
    "port": 5432
}

# ===============================
# STEP 1: CREATE DATABASE
# ===============================

def create_database():
    conn = psycopg2.connect(**ADMIN_DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        cur.execute(f"CREATE DATABASE {APP_DB_NAME};")
        print(f"[OK] Database '{APP_DB_NAME}' created")
    except Exception:
        print(f"[INFO] Database '{APP_DB_NAME}' already exists")

    cur.close()
    conn.close()

# ===============================
# STEP 2: CREATE TABLES
# ===============================

def create_tables():
    conn = psycopg2.connect(**APP_DB_CONFIG)
    cur = conn.cursor()

    # ---- STOCK MASTER ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_master (
        stock_id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) UNIQUE NOT NULL,
        company_name VARCHAR(150) NOT NULL,
        sector VARCHAR(100),
        exchange VARCHAR(50)
    );
    """)

    # ---- STOCK METRICS (SNAPSHOT) ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_metrics (
        stock_id INT PRIMARY KEY,
        pe_ratio DECIMAL(10,2),
        peg_ratio DECIMAL(10,2),
        promoter_holding DECIMAL(5,2),
        last_updated TIMESTAMP,
        FOREIGN KEY (stock_id)
            REFERENCES stock_master(stock_id)
            ON DELETE CASCADE
    );
    """)

    # ---- QUARTERLY FINANCIALS (TIME SERIES) ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quarterly_financials (
        stock_id INT,
        financial_year INT,
        quarter INT CHECK (quarter BETWEEN 1 AND 4),
        revenue DECIMAL(15,2),
        ebitda DECIMAL(15,2),
        net_profit DECIMAL(15,2),
        PRIMARY KEY (stock_id, financial_year, quarter),
        FOREIGN KEY (stock_id)
            REFERENCES stock_master(stock_id)
            ON DELETE CASCADE
    );
    """)

    # ---- ANALYST TARGETS (OPTIONAL) ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS analyst_targets (
        stock_id INT PRIMARY KEY,
        target_price_low DECIMAL(10,2),
        target_price_high DECIMAL(10,2),
        current_price DECIMAL(10,2),
        last_updated TIMESTAMP,
        FOREIGN KEY (stock_id)
            REFERENCES stock_master(stock_id)
            ON DELETE CASCADE
    );
    """)

    # ---- USERS ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        email VARCHAR(150) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ---- PORTFOLIO ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        portfolio_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        stock_id INT NOT NULL,
        average_price DECIMAL(10,2),
        quantity INT,
        FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON DELETE CASCADE,
        FOREIGN KEY (stock_id)
            REFERENCES stock_master(stock_id)
            ON DELETE CASCADE
    );
    """)

    # ---- ALERTS ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        stock_id INT NOT NULL,
        alert_condition TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON DELETE CASCADE,
        FOREIGN KEY (stock_id)
            REFERENCES stock_master(stock_id)
            ON DELETE CASCADE
    );
    """)

    # ===============================
    # INDEXES (PERFORMANCE)
    # ===============================

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_quarterly_stock_year
    ON quarterly_financials(stock_id, financial_year);
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("[OK] All tables and indexes created")

# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    create_database()
    create_tables()
