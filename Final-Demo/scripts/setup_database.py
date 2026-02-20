import psycopg2
from psycopg2 import sql

DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

def setup_database():
    """Create all required tables for the application"""
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cur = conn.cursor()
    
    try:
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Users table created/verified")
        
        # Create query_history table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                query_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                nl_query TEXT NOT NULL,
                dsl JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Query history table created/verified")
        
        # Create stocks table if needed
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                stock_id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) UNIQUE NOT NULL,
                company_name VARCHAR(255) NOT NULL,
                sector VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Stocks table created/verified")
        
        # Create fundamentals table if needed
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fundamentals (
                fundamental_id SERIAL PRIMARY KEY,
                stock_id INTEGER NOT NULL REFERENCES stocks(stock_id) ON DELETE CASCADE,
                pe_ratio FLOAT,
                peg_ratio FLOAT,
                dividend_yield FLOAT,
                debt_to_equity FLOAT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Fundamentals table created/verified")
        
        conn.commit()
        print("\n✅ Database setup completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error setting up database: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    setup_database()
