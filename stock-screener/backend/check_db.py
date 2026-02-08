import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Manual config since we are outside app
DB_CONFIG = {
    "host": "localhost",
    "database": "stock_screener",
    "user": "postgres",
    "password": "Sabeshpostgres@51",
    "port": "5432"
}

def check_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Checking fundamentals table...")
        cur.execute("SELECT * FROM fundamentals LIMIT 5")
        rows = cur.fetchall()
        
        colnames = [desc[0] for desc in cur.description]
        print("Columns:", colnames)
        
        for row in rows:
            print(row)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
