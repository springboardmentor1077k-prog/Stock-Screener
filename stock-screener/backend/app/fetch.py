import yfinance as yf
import psycopg2
from datetime import date
import logging
import sys
import os
from dotenv import load_dotenv

# Ensure we can import from app if running as script from backend/
# This assumes the script is run from 'stock-screener/backend' or 'stock-screener/backend/app'
# We add the parent directory to path to allow 'from app.core import ...' if run from backend/
# backend/app/fetch.py -> backend/app -> backend -> root (if we want to use root as base?)
# Usually 'backend' is the package root if we run 'python -m app.fetch'.
# But if we run 'python backend/app/fetch.py' from root, we need to add 'backend' to path.
current_dir = os.path.dirname(os.path.abspath(__file__)) # backend/app
backend_dir = os.path.dirname(current_dir) # backend
root_dir = os.path.dirname(backend_dir) # stock-screener

sys.path.append(backend_dir) # Allow 'from app.core import ...'

# Load .env explicitly to ensure pydantic finds it
env_path = os.path.join(backend_dir, ".env")
load_dotenv(env_path)

try:
    from app.core import settings
except ImportError:
    print("⚠ Could not import app.core.settings. Check sys.path or .env")
    sys.exit(1)

# ---------------- LOGGING CONFIG ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ---------------- DATABASE CONFIG ----------------
# Use settings from app.core which should load from .env
DB_URI = settings.DATABASE_URI
# If password is separate, we might need to inject it, but the URI usually has it.
# Check if URI is default (which might be wrong) vs env.
if "postgres:postgres" in DB_URI and settings.DATABASE_PASSWORD:
     # If default URI is present but we have a password, we might need to construct URI or rely on env being correct.
     # But we expect .env to provide the FULL correct URI.
     pass

# ---------------- CONNECT DB ----------------
try:
    conn = psycopg2.connect(DB_URI)
    conn.autocommit = False 
    logger.info(f"✅ Connected to database successfully using URI from settings")
except Exception as e:
    logger.error(f"❌ Database connection failed with settings URI. Error: {e}")
    # Fallback to manual construction if env var was just password? 
    # The user asked to "retrieve using that environment variable".
    if settings.DATABASE_PASSWORD:
        logger.info("🔄 Retrying with password from settings...")
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="stock_screener",
                user="postgres",
                password=settings.DATABASE_PASSWORD,
                port="5432"
            )
            conn.autocommit = False
            logger.info("✅ Connected to database using DATABASE_PASSWORD")
        except Exception as retry_e:
            logger.error(f"❌ Retry failed: {retry_e}")
            sys.exit(1)
    else:
        sys.exit(1)
            
cursor = conn.cursor()

# ---------------- INSERT FUNCTION ----------------
def insert_stock(symbol):
    logger.info(f"🔍 Fetching data for {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
    except Exception as e:
        logger.error(f"❌ Failed to fetch data from yfinance for {symbol}: {e}")
        return

    # ---------- CHECK IF STOCK EXISTS ----------
    try:
        cursor.execute("SELECT id FROM stock WHERE symbol = %s", (symbol,))
        row = cursor.fetchone()

        if row:
            stock_id = row[0]
            logger.warning(f"⚠ {symbol} already exists (id={stock_id}), skipping stock insert")
            return
    except Exception as e:
        logger.error(f"❌ Error checking stock existence: {e}")
        conn.rollback()
        return

    # ---------- INSERT STOCK ----------
    try:
        cursor.execute("""
            INSERT INTO stock
            (symbol, company_name, sector, industry, exchange, market_cap, listing_date, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            symbol,
            info.get("longName"),
            info.get("sector"),
            info.get("industry"),
            info.get("exchange"),
            info.get("marketCap"),
            date.today(),
            "ACTIVE"
        ))
        
        stock_id = cursor.fetchone()[0]
        logger.info(f"✨ Inserted stock record for {symbol} (id={stock_id})")

        # ---------- INSERT FUNDAMENTALS ----------
        cursor.execute("""
            INSERT INTO fundamentals
            (stock_id, market_cap, pe_ratio, div_yield, current_price)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            stock_id,
            info.get("marketCap"),
            info.get("trailingPE"),
            info.get("dividendYield"),
            info.get("currentPrice")
        ))
        logger.info(f"📊 Inserted fundamentals for {symbol}")

        # ---------- INSERT FINANCIALS ----------
        financials = ticker.quarterly_financials

        if financials is not None and not financials.empty:
            count = 0
            for col in financials.columns[:4]:
                period = col.to_pydatetime()
                quarter = (period.month - 1) // 3 + 1
                year = period.year

                # Safe safe access to dataframe
                def get_val(df, row_label, col_label):
                    try:
                        if row_label in df.index:
                            val = df.loc[row_label, col_label]
                            # Convert numpy types to python native types
                            if hasattr(val, "item"): 
                                return val.item()
                            return float(val)
                    except Exception:
                        pass
                    return None

                total_revenue = get_val(financials, "Total Revenue", col)
                ebitda = get_val(financials, "EBITDA", col)
                net_income = get_val(financials, "Net Income", col)

                cursor.execute("""
                    INSERT INTO financials
                    (stock_id, quarter_no, fiscal_year, revenue_generated, ebitda, net_profit)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    stock_id,
                    quarter,
                    year,
                    total_revenue,
                    ebitda,
                    net_income
                ))
                count += 1
            logger.info(f"💰 Inserted {count} financial records for {symbol}")
        
        conn.commit()
        logger.info(f"✅ Successfully completed {symbol}")

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Database error while processing {symbol}: {e}")
# "TCS.NS","INFY.NS","RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","AXISBANK.NS",
#     "KOTAKBANK.NS","LT.NS","ITC.NS","HINDUNILVR.NS","BHARTIARTL.NS","ASIANPAINT.NS",
#     "MARUTI.NS","SUNPHARMA.NS","TITAN.NS","ULTRACEMCO.NS","WIPRO.NS","HCLTECH.NS",
#     "BAJFINANCE.NS","BAJAJFINSV.NS","NTPC.NS","POWERGRID.NS","ONGC.NS","TATAMOTORS.NS",
#     "M&M.NS","ADANIENT.NS","ADANIPORTS.NS",
# ---------------- MAIN ----------------
if __name__ == "__main__":
    stocks = [
    "ADANIGREEN.NS","COALINDIA.NS",
    "HINDALCO.NS","JSWSTEEL.NS","TATASTEEL.NS","VEDL.NS","GRASIM.NS","BPCL.NS",
    "IOC.NS","GAIL.NS","INDUSINDBK.NS","TECHM.NS","DIVISLAB.NS","DRREDDY.NS",
    "CIPLA.NS","APOLLOHOSP.NS","EICHERMOT.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS",
    "BRITANNIA.NS","NESTLEIND.NS","DABUR.NS","GODREJCP.NS","PIDILITIND.NS",
    "DMART.NS","HAVELLS.NS","AMBUJACEM.NS","ACC.NS","SHREECEM.NS","UPL.NS",
    "SBILIFE.NS","HDFCLIFE.NS","ICICIPRULI.NS","BAJAJHLDNG.NS","CHOLAFIN.NS",
    "SRF.NS","TORNTPHARM.NS","LUPIN.NS","ALKEM.NS","AUROPHARMA.NS","GLENMARK.NS",
    "BANDHANBNK.NS","IDFCFIRSTB.NS","PNB.NS","BANKBARODA.NS","CANBK.NS",
    "FEDERALBNK.NS","RBLBANK.NS","YESBANK.NS","IRCTC.NS","HAL.NS","BEL.NS",
    "BHEL.NS","LTIM.NS","MPHASIS.NS","COFORGE.NS","PERSISTENT.NS","MINDTREE.NS",
    "ZOMATO.NS","PAYTM.NS","NYKAA.NS","POLYCAB.NS","KEI.NS","VOLTAS.NS",
    "WHIRLPOOL.NS","BOSCHLTD.NS","SIEMENS.NS","ABB.NS","TATAPOWER.NS",
    "NHPC.NS","SJVN.NS","RECLTD.NS","PFC.NS","ASHOKLEY.NS","TVSMOTOR.NS",
    "EXIDEIND.NS","AMARAJABAT.NS","MRF.NS","PAGEIND.NS","TRENT.NS",
    "JUBLFOOD.NS","NAUKRI.NS","INDIGO.NS","DLF.NS","GODREJPROP.NS",
    "OBEROIRLTY.NS","PHOENIXLTD.NS","SUNTV.NS","ZEEL.NS","TV18BRDCST.NS"
    ]

    logger.info("🚀 Starting stock fetch process...")
    for s in stocks:
        insert_stock(s)
    
    cursor.close()
    conn.close()
    logger.info("👋 Done.")

