import yfinance as yf
import psycopg2
from datetime import date

# ✅ PostgreSQL connection
conn = psycopg2.connect(
    dbname="stock_screener",
    user="postgres",
    password="123456",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# ✅ List of NSE stocks (add more anytime)
symbols = [
    "INFY.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "RELIANCE.NS",
    "ITC.NS",
    "SBIN.NS",
    "WIPRO.NS",
    "LT.NS",
    "BHARTIARTL.NS"
]

# ---------------------------------------------------------
# ✅ Insert Company + Fundamentals into DB
# ---------------------------------------------------------
def save_company(symbol):

    stock = yf.Ticker(symbol)
    info = stock.info

    company_name = info.get("shortName", "Unknown")
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")

    pe_ratio = info.get("trailingPE", 0) or 0
    revenue = info.get("totalRevenue", 0) or 0
    eps = info.get("trailingEps", 0) or 0

    # ✅ Convert symbol INFY.NS → INFY
    clean_symbol = symbol.split(".")[0]

    print(f"Fetching {clean_symbol}...")

    # ✅ Insert into company_master
    cur.execute("""
        INSERT INTO company_master(symbol, company_name, sector, industry)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (symbol) DO NOTHING
    """, (clean_symbol, company_name, sector, industry))

    conn.commit()

    # ✅ Get company_id
    cur.execute("SELECT company_id FROM company_master WHERE symbol=%s", (clean_symbol,))
    company_id = cur.fetchone()[0]

    # ✅ Insert into fundamental_data
    cur.execute("""
        INSERT INTO fundamental_data(company_id, pe_ratio, eps, revenue, record_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (company_id, pe_ratio, eps, revenue, date.today()))

    conn.commit()

    print(f"✅ Saved {clean_symbol} into database!\n")


# ---------------------------------------------------------
# ✅ Main Execution
# ---------------------------------------------------------
if __name__ == "__main__":

    for sym in symbols:
        save_company(sym)

    cur.close()
    conn.close()

    print("🎉 Yahoo Finance Sync Completed Successfully!")
