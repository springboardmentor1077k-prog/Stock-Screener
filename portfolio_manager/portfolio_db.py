import sqlite3
import os
import datetime

# Define path to the existing database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Navigate up one level to Stock-Screener, then into analyst_demo
DB_PATH = os.path.join(BASE_DIR, '..', 'analyst_demo', 'stocks.db')

def init_portfolio_tables():
    print(f"Checking database at: {os.path.abspath(DB_PATH)}")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Connected to database successfully.")

    # Create Portfolios table
    # Schema: id, user_id, name, created_at
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Table 'portfolios' check/creation done.")

    # Create Portfolio Holdings table
    # Schema: id, portfolio_id, stock_id, quantity, avg_buy_price, created_at, updated_at
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL,
            stock_id TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_buy_price REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
            FOREIGN KEY (stock_id) REFERENCES stocks(symbol)
        )
    """)
    print("Table 'portfolio_holdings' check/creation done.")

    # Insert Dummy Data if tables are empty
    cursor.execute("SELECT count(*) FROM portfolios")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Inserting mock portfolio data...")
        
        # Mock Portfolios
        # user_id 101, 102
        portfolios = [
            (101, 'My Retirement Fund'),
            (101, 'High Growth Tech'),
            (102, 'Safe Dividends')
        ]
        cursor.executemany("INSERT INTO portfolios (user_id, name) VALUES (?, ?)", portfolios)
        
        # Get the IDs of the inserted portfolios
        # We can assume they are 1, 2, 3 since it's a fresh table with autoincrement
        
        # Mock Holdings
        # Portfolio 1 (Retirement): AAPL, MSFT
        # Portfolio 2 (Tech): NVDA, TSLA
        # Portfolio 3 (Dividends): JPM, XOM
        
        holdings = [
            (1, 'AAPL', 50.0, 150.25),
            (1, 'MSFT', 30.0, 310.50),
            (2, 'NVDA', 15.0, 450.00),
            (2, 'TSLA', 20.0, 240.80),
            (3, 'JPM', 100.0, 145.00),
            (3, 'XOM', 200.0, 105.50)
        ]
        
        cursor.executemany("""
            INSERT INTO portfolio_holdings (portfolio_id, stock_id, quantity, avg_buy_price) 
            VALUES (?, ?, ?, ?)
        """, holdings)
        print(f"Inserted {len(portfolios)} portfolios and {len(holdings)} holdings.")
    else:
        print("Portfolios table already contains data. Skipping mock insertion.")

    conn.commit()
    conn.close()
    print("Portfolio tables setup complete.")

if __name__ == "__main__":
    init_portfolio_tables()
