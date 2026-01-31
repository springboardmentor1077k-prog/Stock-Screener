import sqlite3
import random
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "stocks.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Drop tables if exist to reset state
    cursor.execute("DROP TABLE IF EXISTS analyst_ratings")
    cursor.execute("DROP TABLE IF EXISTS stocks")

    # Create stocks table
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

    # Create analyst_ratings table
    cursor.execute("""
        CREATE TABLE analyst_ratings (
            symbol TEXT PRIMARY KEY,
            target_price REAL,
            recommendation TEXT,
            disclaimer TEXT,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol)
        )
    """)

    # 1. Define Base Data (Real Tickers)
    base_stocks = [
        # IT
        ('AAPL', 'Apple Inc.', 'IT'), ('MSFT', 'Microsoft Corp.', 'IT'), ('GOOGL', 'Alphabet Inc.', 'IT'),
        ('NVDA', 'NVIDIA Corp.', 'IT'), ('ORCL', 'Oracle Corp.', 'IT'), ('CSCO', 'Cisco Systems', 'IT'),
        ('ADBE', 'Adobe Inc.', 'IT'), ('CRM', 'Salesforce', 'IT'), ('INTC', 'Intel Corp.', 'IT'),
        ('AMD', 'Advanced Micro Devices', 'IT'), ('IBM', 'IBM', 'IT'), ('QCOM', 'Qualcomm', 'IT'),
        # Finance
        ('JPM', 'JPMorgan Chase', 'Finance'), ('BAC', 'Bank of America', 'Finance'), ('V', 'Visa Inc.', 'Finance'),
        ('MA', 'Mastercard', 'Finance'), ('WFC', 'Wells Fargo', 'Finance'), ('C', 'Citigroup', 'Finance'),
        ('GS', 'Goldman Sachs', 'Finance'), ('MS', 'Morgan Stanley', 'Finance'), ('AXP', 'American Express', 'Finance'),
        ('BLK', 'BlackRock', 'Finance'),
        # Healthcare
        ('JNJ', 'Johnson & Johnson', 'Healthcare'), ('PFE', 'Pfizer Inc.', 'Healthcare'), ('UNH', 'UnitedHealth', 'Healthcare'),
        ('LLY', 'Eli Lilly', 'Healthcare'), ('ABBV', 'AbbVie', 'Healthcare'), ('MRK', 'Merck & Co.', 'Healthcare'),
        ('TMO', 'Thermo Fisher', 'Healthcare'), ('DHR', 'Danaher Corp.', 'Healthcare'), ('ABT', 'Abbott Labs', 'Healthcare'),
        # Energy
        ('XOM', 'Exxon Mobil', 'Energy'), ('CVX', 'Chevron Corp.', 'Energy'), ('SHEL', 'Shell PLC', 'Energy'),
        ('TTE', 'TotalEnergies', 'Energy'), ('COP', 'ConocoPhillips', 'Energy'), ('SLB', 'Schlumberger', 'Energy'),
        ('EOG', 'EOG Resources', 'Energy'), ('MPC', 'Marathon Petroleum', 'Energy'),
        # Consumer Discretionary
        ('AMZN', 'Amazon.com', 'Consumer Discretionary'), ('TSLA', 'Tesla Inc.', 'Consumer Discretionary'),
        ('HD', 'Home Depot', 'Consumer Discretionary'), ('MCD', 'McDonalds', 'Consumer Discretionary'),
        ('NKE', 'Nike Inc.', 'Consumer Discretionary'), ('SBUX', 'Starbucks', 'Consumer Discretionary'),
        ('LOW', 'Lowe\'s', 'Consumer Discretionary'), ('TGT', 'Target Corp.', 'Consumer Discretionary'),
        # Consumer Staples
        ('PG', 'Procter & Gamble', 'Consumer Staples'), ('KO', 'Coca-Cola', 'Consumer Staples'),
        ('PEP', 'PepsiCo', 'Consumer Staples'), ('COST', 'Costco', 'Consumer Staples'),
        ('WMT', 'Walmart', 'Consumer Staples'),
        # Industrials
        ('CAT', 'Caterpillar', 'Industrials'), ('UNP', 'Union Pacific', 'Industrials'),
        ('UPS', 'United Parcel Service', 'Industrials'), ('BA', 'Boeing', 'Industrials'),
        ('GE', 'General Electric', 'Industrials')
    ]

    all_stocks_data = []
    all_analyst_data = []

    disclaimers = [
        "Investing involves risk. Past performance does not guarantee future results.",
        "Analyst ratings are subjective opinions.",
        "Market conditions may affect target prices.",
        "High volatility expected in this sector.",
        "Based on projected earnings growth.",
        "Subject to regulatory approvals.",
        "Currency fluctuations may impact returns.",
        "Supply chain risks remain a factor."
    ]

    # Generate data for defined stocks + some synthetic ones to reach ~100 records
    
    # First, process the real base stocks
    for symbol, name, sector in base_stocks:
        price = round(random.uniform(20.0, 500.0), 2)
        market_cap = round(random.uniform(10.0, 3000.0), 2) # Billions
        pe_ratio = round(random.uniform(5.0, 80.0), 2)
        
        all_stocks_data.append((symbol, name, sector, price, market_cap, pe_ratio))
        
        # Generate Analyst Data
        # Target price logic: +/- 30% of current price
        target_price = round(price * random.uniform(0.7, 1.4), 2)
        upside = (target_price - price) / price
        
        if upside > 0.20:
            recommendation = "Strong Buy"
        elif upside > 0.10:
            recommendation = "Buy"
        elif upside > -0.10:
            recommendation = "Hold"
        elif upside > -0.20:
            recommendation = "Sell"
        else:
            recommendation = "Strong Sell"
            
        disclaimer = random.choice(disclaimers)
        all_analyst_data.append((symbol, target_price, recommendation, disclaimer))

    # Second, generate synthetic stocks to bulk up the data
    sectors = ['IT', 'Finance', 'Healthcare', 'Energy', 'Consumer Discretionary', 'Industrials', 'Utilities', 'Materials']
    
    for i in range(1, 51): # Add 50 synthetic stocks
        symbol = f"SYN{i:03d}"
        sector = random.choice(sectors)
        name = f"Synthetic {sector} Corp {i}"
        
        price = round(random.uniform(10.0, 200.0), 2)
        market_cap = round(random.uniform(1.0, 50.0), 2)
        pe_ratio = round(random.uniform(5.0, 50.0), 2)
        
        all_stocks_data.append((symbol, name, sector, price, market_cap, pe_ratio))
        
        # Analyst Data for synthetic
        target_price = round(price * random.uniform(0.6, 1.5), 2)
        upside = (target_price - price) / price
        
        if upside > 0.20:
            recommendation = "Strong Buy"
        elif upside > 0.10:
            recommendation = "Buy"
        elif upside > -0.10:
            recommendation = "Hold"
        elif upside > -0.20:
            recommendation = "Sell"
        else:
            recommendation = "Strong Sell"
            
        disclaimer = random.choice(disclaimers)
        all_analyst_data.append((symbol, target_price, recommendation, disclaimer))

    # Batch Insert Stocks
    cursor.executemany("""
        INSERT INTO stocks (symbol, company_name, sector, price, market_cap, pe_ratio)
        VALUES (?, ?, ?, ?, ?, ?)
    """, all_stocks_data)

    # Batch Insert Analyst Ratings
    cursor.executemany("""
        INSERT INTO analyst_ratings (symbol, target_price, recommendation, disclaimer)
        VALUES (?, ?, ?, ?)
    """, all_analyst_data)

    conn.commit()
    print(f"Database {DB_NAME} initialized successfully.")
    print(f"Inserted {len(all_stocks_data)} stock records.")
    print(f"Inserted {len(all_analyst_data)} analyst rating records.")
    
    conn.close()

if __name__ == "__main__":
    init_db()
