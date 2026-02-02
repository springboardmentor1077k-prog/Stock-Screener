import sqlite3
import random

DB_NAME = "stocks.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Drop table if exists to reset state
    cursor.execute("DROP TABLE IF EXISTS stocks")

    # Create table
    cursor.execute("""
        CREATE TABLE stocks (
            symbol TEXT PRIMARY KEY,
            company_name TEXT,
            sector TEXT,
            price REAL,
            market_cap REAL,
            pe_ratio REAL
        )
    """)

    # Create analyst table
    cursor.execute("DROP TABLE IF EXISTS analyst_ratings")
    cursor.execute("""
        CREATE TABLE analyst_ratings (
            symbol TEXT PRIMARY KEY,
            target_price REAL,
            recommendation TEXT,
            disclaimer TEXT,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol)
        )
    """)

    # Sample data generation
    sectors = ['IT', 'Finance', 'Healthcare', 'Energy', 'Consumer Discretionary']
    
    # Specific realistic records to ensure demo queries work
    initial_data = [
        ('AAPL', 'Apple Inc.', 'IT', 175.50, 2800.0, 28.5),
        ('MSFT', 'Microsoft Corp.', 'IT', 320.0, 2400.0, 32.1),
        ('GOOGL', 'Alphabet Inc.', 'IT', 140.0, 1800.0, 24.8),
        ('NVDA', 'NVIDIA Corp.', 'IT', 450.0, 1100.0, 65.4),
        ('JPM', 'JPMorgan Chase', 'Finance', 145.0, 420.0, 10.5),
        ('BAC', 'Bank of America', 'Finance', 28.5, 230.0, 9.2),
        ('V', 'Visa Inc.', 'Finance', 240.0, 500.0, 30.1),
        ('JNJ', 'Johnson & Johnson', 'Healthcare', 155.0, 400.0, 15.6),
        ('PFE', 'Pfizer Inc.', 'Healthcare', 32.0, 180.0, 12.4),
        ('XOM', 'Exxon Mobil', 'Energy', 110.0, 440.0, 11.2),
        ('CVX', 'Chevron Corp.', 'Energy', 160.0, 300.0, 10.8),
        ('AMZN', 'Amazon.com', 'Consumer Discretionary', 130.0, 1300.0, 40.5),
        ('TSLA', 'Tesla Inc.', 'Consumer Discretionary', 240.0, 750.0, 70.2),
    ]

    cursor.executemany("""
        INSERT INTO stocks (symbol, company_name, sector, price, market_cap, pe_ratio)
        VALUES (?, ?, ?, ?, ?, ?)
    """, initial_data)

    # Insert mock analyst data for 5 stocks
    analyst_data = [
        ('AAPL', 200.0, 'Strong Buy', 'Investing involves risk. Past performance does not guarantee future results.'),
        ('MSFT', 400.0, 'Buy', 'Analyst ratings are subjective opinions.'),
        ('GOOGL', 160.0, 'Buy', 'Market conditions may affect target prices.'),
        ('NVDA', 600.0, 'Strong Buy', 'High volatility expected in semiconductor sector.'),
        ('TSLA', 300.0, 'Hold', 'Automotive industry faces supply chain challenges.')
    ]
    
    cursor.executemany("""
        INSERT INTO analyst_ratings (symbol, target_price, recommendation, disclaimer)
        VALUES (?, ?, ?, ?)
    """, analyst_data)

    # Add more random data to reach "hundreds" or at least a decent amount
    extra_companies = [
        ('ORCL', 'Oracle', 'IT'), ('CSCO', 'Cisco', 'IT'), ('ADBE', 'Adobe', 'IT'),
        ('CRM', 'Salesforce', 'IT'), ('INTC', 'Intel', 'IT'), ('AMD', 'AMD', 'IT'),
        ('WFC', 'Wells Fargo', 'Finance'), ('C', 'Citigroup', 'Finance'), ('GS', 'Goldman Sachs', 'Finance'),
        ('MS', 'Morgan Stanley', 'Finance'), ('AXP', 'American Express', 'Finance'),
        ('UNH', 'UnitedHealth', 'Healthcare'), ('LLY', 'Eli Lilly', 'Healthcare'), ('ABBV', 'AbbVie', 'Healthcare'),
        ('MRK', 'Merck', 'Healthcare'), ('TMO', 'Thermo Fisher', 'Healthcare'),
        ('SHEL', 'Shell', 'Energy'), ('TTE', 'TotalEnergies', 'Energy'), ('COP', 'ConocoPhillips', 'Energy'),
        ('SLB', 'Schlumberger', 'Energy'), ('EOG', 'EOG Resources', 'Energy'),
        ('HD', 'Home Depot', 'Consumer Discretionary'), ('MCD', 'McDonalds', 'Consumer Discretionary'),
        ('NKE', 'Nike', 'Consumer Discretionary'), ('SBUX', 'Starbucks', 'Consumer Discretionary')
    ]

    extra_data = []
    # Generate ~200 records
    count = 0
    for _ in range(8):
        for symbol_base, name_base, sector in extra_companies:
            count += 1
            symbol = f"{symbol_base}{count}"
            name = f"{name_base} {count}"
            
            price = round(random.uniform(20, 500), 2)
            market_cap = round(random.uniform(50, 1000), 2)
            pe_ratio = round(random.uniform(5, 80), 2)
            extra_data.append((symbol, name, sector, price, market_cap, pe_ratio))

    cursor.executemany("""
        INSERT INTO stocks (symbol, company_name, sector, price, market_cap, pe_ratio)
        VALUES (?, ?, ?, ?, ?, ?)
    """, extra_data)

    conn.commit()
    print(f"Database {DB_NAME} initialized with {len(initial_data) + len(extra_data)} records.")
    conn.close()

if __name__ == "__main__":
    init_db()
