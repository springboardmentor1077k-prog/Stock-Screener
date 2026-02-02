import sqlite3
import pandas as pd
import os
try:
    from config import DB_PATH
except ImportError:
    from .config import DB_PATH

TABLE_NAME = "analyst_ratings"

def get_schema():
    return """
    CREATE TABLE IF NOT EXISTS analyst_ratings (
        symbol TEXT PRIMARY KEY,
        target_price REAL,
        recommendation TEXT,
        disclaimer TEXT,
        FOREIGN KEY (symbol) REFERENCES stocks(symbol)
    )
    """

def show_table():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        print(f"--- Table: {TABLE_NAME} ---")
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
        if df.empty:
            print("No data found.")
        else:
            try:
                print(df.to_markdown(index=False))
            except (ImportError, AttributeError):
                print(df.to_string(index=False))
        print(f"\nTotal Records: {len(df)}")
    except Exception as e:
        print(f"Error reading table {TABLE_NAME}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_table()
