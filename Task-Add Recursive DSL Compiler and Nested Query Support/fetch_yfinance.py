import yfinance as yf
import psycopg2
import pandas as pd
from datetime import datetime
import time
import zlib

# --- CONFIGURATION ---
SYMBOLS = [
    "MSFT", "AAPL", "NVDA", "GOOGL", "META", "AMD", "INTC",
    "JPM", "BAC", "V", "MA",
    "AMZN", "TSLA", "WMT", "KO", "PEP",
    "JNJ", "PFE", "UNH", "XOM"
]

DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG)

def generate_id(ticker):
    """Generates a stable integer ID (masked to fit PostgreSQL INTEGER)."""
    return zlib.crc32(ticker.encode()) & 0x7FFFFFFF

def safe_float(val):
    """Safely convert numpy/pandas types to standard float for DB"""
    if pd.isna(val) or val is None:
        return None
    return float(val)

def fetch_and_store_yfinance():
    conn = get_db_connection()
    cur = conn.cursor()
    print(f"🚀 Starting yfinance data fetch for {len(SYMBOLS)} symbols...")

    for ticker_symbol in SYMBOLS:
        try:
            print(f"\n📡 Fetching {ticker_symbol}...")
            stock = yf.Ticker(ticker_symbol)
            
            # 1. FETCH INFO
            try:
                info = stock.info
            except Exception as e:
                print(f"   ⚠️ Could not fetch info for {ticker_symbol}: {e}")
                continue
            
            stock_id = generate_id(ticker_symbol)
            
            # --- UPSERT STOCK ---
            cur.execute("SELECT stock_id FROM stocks WHERE ticker = %s", (ticker_symbol,))
            res = cur.fetchone()
            if res:
                stock_id = res[0]
                print(f"   Using existing ID {stock_id}...")
                cur.execute("""
                    UPDATE stocks SET company_name=%s, sector=%s 
                    WHERE stock_id=%s
                """, (info.get('longName'), info.get('sector'), stock_id))
            else:
                print(f"   Creating new ID {stock_id}...")
                cur.execute("""
                    INSERT INTO stocks (stock_id, ticker, company_name, sector)
                    VALUES (%s, %s, %s, %s)
                """, (stock_id, ticker_symbol, info.get('longName'), info.get('sector')))

            # --- UPSERT FUNDAMENTALS (ROBUST PEG LOGIC) ---
            pe = safe_float(info.get('trailingPE'))
            
            # 1. Try standard key
            peg = safe_float(info.get('pegRatio'))
            
            # 2. Fallback: Try trailing PEG key
            if peg is None:
                peg = safe_float(info.get('trailingPegRatio'))
                
            # 3. Fallback: Estimate PEG = P/E / (EarningsGrowth * 100)
            if peg is None and pe is not None:
                growth = safe_float(info.get('earningsGrowth')) # e.g., 0.15 for 15%
                if growth and growth > 0:
                    try:
                        peg = pe / (growth * 100)
                        print(f"   ℹ️ Calculated PEG estimate: {peg:.2f}")
                    except ZeroDivisionError:
                        pass

            div_yield = safe_float(info.get('dividendYield')) 
            debt_to_equity = safe_float(info.get('debtToEquity'))

            cur.execute("""
                INSERT INTO fundamentals (stock_id, pe_ratio, peg_ratio, dividend_yield, debt_to_equity, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (stock_id) 
                DO UPDATE SET 
                    pe_ratio=EXCLUDED.pe_ratio, 
                    peg_ratio=EXCLUDED.peg_ratio, 
                    dividend_yield=EXCLUDED.dividend_yield,
                    debt_to_equity=EXCLUDED.debt_to_equity,
                    updated_at=NOW();
            """, (stock_id, pe, peg, div_yield, debt_to_equity))
            print("   ✅ Fundamentals updated")

            # --- UPSERT QUARTERLY FINANCIALS ---
            q_fin = stock.quarterly_income_stmt
            
            if q_fin is not None and not q_fin.empty:
                q_fin = q_fin.T 
                count = 0
                for date_idx, row in q_fin.iterrows():
                    year = date_idx.year
                    quarter = (date_idx.month - 1) // 3 + 1
                    
                    revenue = safe_float(row.get('Total Revenue'))
                    net_profit = safe_float(row.get('Net Income'))
                    
                    # EBITDA fallback
                    ebitda = safe_float(row.get('EBITDA'))
                    if ebitda is None:
                         ebitda = safe_float(row.get('Normalized EBITDA'))

                    check_sql = "SELECT id FROM quarterly_financials WHERE stock_id=%s AND year=%s AND quarter=%s"
                    cur.execute(check_sql, (stock_id, year, quarter))
                    
                    if cur.fetchone():
                        update_sql = """
                            UPDATE quarterly_financials 
                            SET revenue=%s, net_profit=%s, ebitda=%s
                            WHERE stock_id=%s AND year=%s AND quarter=%s
                        """
                        cur.execute(update_sql, (revenue, net_profit, ebitda, stock_id, year, quarter))
                    else:
                        insert_sql = """
                            INSERT INTO quarterly_financials (stock_id, year, quarter, revenue, net_profit, ebitda)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        cur.execute(insert_sql, (stock_id, year, quarter, revenue, net_profit, ebitda))
                    count += 1
                print(f"   ✅ Updated {count} quarters of history")
            else:
                print("   ⚠️ No quarterly financials found")

            conn.commit()

        except Exception as e:
            print(f"❌ Error fetching {ticker_symbol}: {e}")
            conn.rollback()

    cur.close()
    conn.close()
    print("\n🎉 YFinance Data Load Complete!")

if __name__ == "__main__":
    fetch_and_store_yfinance()