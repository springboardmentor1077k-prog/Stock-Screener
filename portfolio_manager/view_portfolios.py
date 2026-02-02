import sqlite3
import os
import pandas as pd

# Define path to the existing database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'analyst_demo', 'stocks.db')

def view_data():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    print(f"--- Database: {os.path.basename(DB_PATH)} ---")
    print(f"Location: {os.path.abspath(DB_PATH)}\n")

    # View Portfolios
    print("=== Table: portfolios ===")
    try:
        df_portfolios = pd.read_sql_query("SELECT * FROM portfolios", conn)
        if df_portfolios.empty:
            print("No data found.")
        else:
            print(df_portfolios.to_markdown(index=False))
    except Exception as e:
        print(f"Error reading portfolios: {e}")

    print("\n")

    # View Portfolio Holdings
    print("=== Table: portfolio_holdings ===")
    try:
        df_holdings = pd.read_sql_query("SELECT * FROM portfolio_holdings", conn)
        if df_holdings.empty:
            print("No data found.")
        else:
            print(df_holdings.to_markdown(index=False))
    except Exception as e:
        print(f"Error reading portfolio_holdings: {e}")

    conn.close()

if __name__ == "__main__":
    try:
        import tabulate # Required for to_markdown usually, but pandas might handle it or fallback
    except ImportError:
        # Fallback if tabulate is not installed, though it's often with pandas in some envs
        # We'll just print default string representation
        pd.DataFrame.to_markdown = lambda self, index=False: self.to_string(index=index)
        
    view_data()
