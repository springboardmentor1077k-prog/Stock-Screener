import requests
import psycopg2
from datetime import datetime
import time

# --- CONFIGURATION ---
API_KEY = "G7Q1ID8B79L1N84T"
SYMBOL = "PFE"  # Bank of America (Change this to fetch other stocks like MSFT, AAPL)
DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG)

def parse_float(val):
    """Safely parses float strings from API"""
    if val and val != "None" and val != "-":
        return float(val)
    return None

def get_quarter_from_date(date_str):
    """Converts '2023-09-30' to Year (2023) and Quarter (3)"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.year, (dt.month - 1) // 3 + 1
    except ValueError:
        return None, None

def fetch_full_stock_data():
    conn = get_db_connection()
    cur = conn.cursor()
    print(f"🚀 Starting full data fetch for {SYMBOL}...")

    # ======================================================
    # PART 1: FETCH OVERVIEW (Stock Info & Fundamentals)
    # ======================================================
    print("1️⃣ Fetching Company Overview...")
    url_overview = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={SYMBOL}&apikey={API_KEY}"
    res_ov = requests.get(url_overview)
    data_ov = res_ov.json()

    if not data_ov.get("Symbol"):
        print(f"❌ Error: No data found for {SYMBOL}")
        return

    # --- FIX: Check if Ticker Already Exists ---
    ticker = data_ov.get("Symbol")
    cur.execute("SELECT stock_id FROM stocks WHERE ticker = %s", (ticker,))
    existing_stock = cur.fetchone()

    if existing_stock:
        # Case A: Stock exists -> Use EXISTING DB ID (Safe Update)
        stock_id = existing_stock[0]
        print(f"⚠️ Found existing {SYMBOL} with ID {stock_id}. Updating it...")
        
        cur.execute("""
            UPDATE stocks 
            SET company_name=%s, sector=%s 
            WHERE stock_id=%s
        """, (data_ov.get("Name"), data_ov.get("Sector"), stock_id))
        
    else:
        # Case B: New Stock -> Use API ID (CIK)
        stock_id = int(data_ov.get("CIK", 0))
        if stock_id == 0:
            print("❌ Error: API did not return a valid ID (CIK).")
            return

        print(f"✨ Inserting NEW stock {SYMBOL} with ID {stock_id}...")
        cur.execute("""
            INSERT INTO stocks (stock_id, ticker, company_name, sector)
            VALUES (%s, %s, %s, %s)
        """, (stock_id, ticker, data_ov.get("Name"), data_ov.get("Sector")))


    # 1.2 Insert/Update FUNDAMENTALS table
    updated_at_date = None
    if data_ov.get("LatestQuarter"):
        try:
            updated_at_date = datetime.strptime(data_ov["LatestQuarter"], "%Y-%m-%d")
        except ValueError:
            updated_at_date = None

    # FIX: Changed 'last_updated' to 'updated_at' to match database schema
    cur.execute("""
        INSERT INTO fundamentals (stock_id, pe_ratio, peg_ratio, updated_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (stock_id) 
        DO UPDATE SET pe_ratio=EXCLUDED.pe_ratio, peg_ratio=EXCLUDED.peg_ratio, updated_at=EXCLUDED.updated_at;
    """, (
        stock_id,
        parse_float(data_ov.get("PERatio")),
        parse_float(data_ov.get("PEGRatio")),
        updated_at_date
    ))
    
    print("✅ Stock Profile & Fundamentals updated.")

    # ======================================================
    # PART 2: FETCH QUARTERLY HISTORY (Income Statement)
    # ======================================================
    print("2️⃣ Fetching Quarterly History...")
    time.sleep(1) # Be nice to API
    
    url_income = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={SYMBOL}&apikey={API_KEY}"
    res_inc = requests.get(url_income)
    data_inc = res_inc.json()

    quarterly_reports = data_inc.get("quarterlyReports", [])
    
    if not quarterly_reports:
        print("⚠️ No quarterly reports found (Check API limit).")
    else:
        count = 0
        for report in quarterly_reports:
            fiscal_date = report.get("fiscalDateEnding")
            if not fiscal_date:
                continue

            year, quarter = get_quarter_from_date(fiscal_date)
            
            # Map API fields to your DB columns
            revenue = parse_float(report.get("totalRevenue"))
            net_profit = parse_float(report.get("netIncome"))
            ebitda = parse_float(report.get("ebitda"))

            # 2.1 Upsert into QUARTERLY_FINANCIALS
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
            
        print(f"✅ Updated {count} historical quarters.")

    conn.commit()
    cur.close()
    conn.close()
    print(f"🎉 All data for {SYMBOL} is now fresh!")

if __name__ == "__main__":
    fetch_full_stock_data()