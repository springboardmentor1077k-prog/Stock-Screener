import yfinance as yf
import psycopg2
import pandas as pd
from datetime import datetime
import time
import zlib

# --- CONFIGURATION ---
# 130+ Symbols across diverse sectors
SYMBOLS = [
    # --- TECHNOLOGY ---
    "MSFT", "AAPL", "NVDA", "GOOGL", "META", "AMD", "INTC", "CSCO", "ORCL", "CRM",
    "ADBE", "AVGO", "QCOM", "TXN", "IBM", "NOW", "AMAT", "MU", "ADI", "LRCX",
    "SNOW", "PLTR", "PANW", "CRWD", "FTNT", "SQ", "SHOP", "ZM", "TEAM", "WDAY",

    # --- FINANCE ---
    "JPM", "BAC", "V", "MA", "WFC", "GS", "MS", "BLK", "C", "AXP",
    "SPGI", "PGR", "CB", "MMC", "AON", "USB", "PNC", "TFC", "COF", "HIG",
    "PYPL", "FIS", "FISV", "GPN", "SOFI", "AFRM", "UPST",

    # --- HEALTHCARE ---
    "JNJ", "PFE", "UNH", "LLY", "MRK", "ABBV", "TMO", "DHR", "ABT", "BMY",
    "AMGN", "GILD", "ISRG", "SYK", "ELV", "CVS", "CI", "HUM", "MCK", "ZTS",
    "REGN", "VRTX", "BSX", "EW", "DXCM", "MDT",

    # --- CONSUMER ---
    "AMZN", "TSLA", "WMT", "KO", "PEP", "PG", "COST", "MCD", "NKE", "SBUX",
    "HD", "LOW", "TGT", "TJX", "LULU", "CMG", "YUM", "DPZ", "DRI",
    "PM", "MO", "CL", "KMB", "EL", "GIS", "K", "MNST", "STZ",

    # --- ENERGY & INDUSTRIAL ---
    "XOM", "CVX", "COP", "CAT", "GE", "UPS", "BA", "HON", "UNP", "DE",
    "LMT", "RTX", "NOC", "GD", "MMM", "ETN", "ITW", "EMR", "PH", "CMI",
    "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HES", "KMI", "WMB",

    # --- UTILITIES & REAL ESTATE ---
    "NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "PEG", "ED",
    "PLD", "AMT", "CCI", "EQIX", "PSA", "O", "SPG", "DLR", "VICI", "WELL"
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
                cur.execute("""
                    UPDATE stocks SET company_name=%s, sector=%s 
                    WHERE stock_id=%s
                """, (info.get('longName'), info.get('sector'), stock_id))
            else:
                cur.execute("""
                    INSERT INTO stocks (stock_id, ticker, company_name, sector)
                    VALUES (%s, %s, %s, %s)
                """, (stock_id, ticker_symbol, info.get('longName'), info.get('sector')))

            # --- UPSERT FUNDAMENTALS ---
            pe = safe_float(info.get('trailingPE'))
            peg = safe_float(info.get('pegRatio'))
            
            # Robust PEG Fallback
            if peg is None:
                peg = safe_float(info.get('trailingPegRatio'))
            if peg is None and pe is not None:
                growth = safe_float(info.get('earningsGrowth'))
                if growth and growth > 0:
                    try:
                        peg = pe / (growth * 100)
                    except: pass

            div_yield = safe_float(info.get('dividendYield'))
            if div_yield and div_yield < 1: 
                div_yield = div_yield * 100 

            debt_to_equity = safe_float(info.get('debtToEquity'))

            # CORRECTED SQL: 'net_profit' is removed to match your schema
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

            # --- UPSERT ANALYST TARGETS ---
            current_price = safe_float(info.get('currentPrice'))
            target_high = safe_float(info.get('targetHighPrice'))
            target_low = safe_float(info.get('targetLowPrice'))
            recommendation = info.get('recommendationKey', 'none')

            if current_price:
                 cur.execute("""
                    INSERT INTO analysis_target (stock_id, current_price, high_target_price, low_target_price, recommendation_key, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (stock_id)
                    DO UPDATE SET
                        current_price=EXCLUDED.current_price,
                        high_target_price=EXCLUDED.high_target_price,
                        low_target_price=EXCLUDED.low_target_price,
                        recommendation_key=EXCLUDED.recommendation_key,
                        updated_at=NOW();
                """, (stock_id, current_price, target_high, target_low, recommendation))
                 print("   ✅ Analyst Targets updated")

            conn.commit()

        except Exception as e:
            print(f"❌ Error fetching {ticker_symbol}: {e}")
            conn.rollback()

    cur.close()
    conn.close()
    print("\n🎉 YFinance Data Load Complete!")

if __name__ == "__main__":
    fetch_and_store_yfinance()