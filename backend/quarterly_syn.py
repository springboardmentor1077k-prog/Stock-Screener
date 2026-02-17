import yfinance as yf
from sqlalchemy import create_engine, text
from config import DATABASE_URL

# -----------------------------------------
# Database Engine
# -----------------------------------------
engine = create_engine(DATABASE_URL)


# -----------------------------------------
# Convert month → Quarter
# -----------------------------------------
def get_quarter(month):
    if month in [1, 2, 3]:
        return "Q1"
    elif month in [4, 5, 6]:
        return "Q2"
    elif month in [7, 8, 9]:
        return "Q3"
    else:
        return "Q4"


# -----------------------------------------
# Fetch company_id from company_master
# -----------------------------------------
def get_company_id(symbol):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT company_id
            FROM company_master
            WHERE symbol = :sym
        """), {"sym": symbol}).fetchone()

        if result:
            return result[0]
        else:
            print(f"❌ {symbol} not found in company_master.")
            return None


# -----------------------------------------
# Insert quarterly data into DB
# -----------------------------------------
def fetch_and_store(yahoo_symbol, company_id):

    print(f"\n📊 Fetching quarterly data for {yahoo_symbol}")

    ticker = yf.Ticker(yahoo_symbol)

    # Use income statement (most reliable)
    quarterly = ticker.quarterly_income_stmt

    if quarterly.empty:
        print("⚠ No quarterly data found.")
        return

    print("✅ Data received from Yahoo.")

    for quarter_date in quarterly.columns:

        try:
            revenue = quarterly.loc["Total Revenue", quarter_date]
            profit = quarterly.loc["Net Income", quarter_date]
        except KeyError:
            print("⚠ Required financial fields not found.")
            continue

        if revenue is None or profit is None:
            continue

        year = quarter_date.year
        month = quarter_date.month
        quarter = get_quarter(month)

        # -----------------------------------------
        # Prevent Duplicate Insertion
        # -----------------------------------------
        with engine.connect() as conn:

            exists = conn.execute(text("""
                SELECT 1 FROM quarterly_financials
                WHERE company_id = :cid
                AND quarter = :qtr
                AND year = :yr
            """), {
                "cid": company_id,
                "qtr": quarter,
                "yr": year
            }).fetchone()

            if exists:
                print(f"⏩ Skipping {quarter} {year} (Already Exists)")
                continue

            conn.execute(text("""
                INSERT INTO quarterly_financials
                (company_id, quarter, year, revenue, profit)
                VALUES (:cid, :qtr, :yr, :rev, :profit)
            """), {
                "cid": company_id,
                "qtr": quarter,
                "yr": year,
                "rev": float(revenue),
                "profit": float(profit)
            })

            conn.commit()

        print(f"✅ Inserted {quarter} {year}")

    print(f"🎉 Done inserting for {yahoo_symbol}")


# -----------------------------------------
# MAIN EXECUTION
# -----------------------------------------
if __name__ == "__main__":

    # Use symbols exactly as stored in company_master
    db_symbols = ["RELIANCE", "TCS", "INFY"]

    for db_symbol in db_symbols:

        company_id = get_company_id(db_symbol)

        if company_id:
            yahoo_symbol = db_symbol + ".NS"
            fetch_and_store(yahoo_symbol, company_id)
