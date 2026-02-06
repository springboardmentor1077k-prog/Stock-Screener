import requests
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import time
import os

# =========================
# CONFIGURATION
# =========================

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "BPT13OE1FRRJVFHY")
BASE_URL = "https://www.alphavantage.co/query"

DB_CONFIG = {
    "dbname": "stocks_db",
    "user": "postgres",
    "password": "Nethra@02",
    "host": "localhost",
    "port": 5432
}

# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# =========================
# STAGE 1: FETCHER
# =========================

def fetch_api(function, symbol):
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        time.sleep(12)  # Alpha Vantage rate limit
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[FETCH ERROR] {symbol} | {e}")
        return None

# =========================
# STAGE 2: VALIDATOR
# =========================

def validate_overview(data):
    required_fields = ["Symbol", "Name", "PERatio", "PEGRatio"]
    for field in required_fields:
        if field not in data or data[field] in ["", None]:
            return False
    return True

def validate_quarterly(report):
    required_fields = ["fiscalDateEnding", "totalRevenue", "ebitda", "netIncome"]
    for field in required_fields:
        if field not in report or report[field] in ["", None]:
            return False
    return True

# =========================
# STAGE 3: NORMALIZER
# =========================

def normalize_overview(data):
    return {
        "symbol": data["Symbol"],
        "company_name": data["Name"],
        "sector": data.get("Sector"),
        "exchange": data.get("Exchange"),
        "pe_ratio": float(data["PERatio"]),
        "peg_ratio": float(data["PEGRatio"])
    }

def normalize_quarterly(report):
    date = report["fiscalDateEnding"]
    year = int(date[:4])
    month = int(date[5:7])
    quarter = (month - 1) // 3 + 1

    return {
        "year": year,
        "quarter": quarter,
        "revenue": float(report["totalRevenue"]),
        "ebitda": float(report["ebitda"]),
        "net_profit": float(report["netIncome"])
    }

# =========================
# STAGE 4: TRANSFORMER
# =========================

def transform_quarterly(stock_id, normalized_reports):
    rows = []
    for r in normalized_reports:
        rows.append((
            stock_id,
            r["year"],
            r["quarter"],
            r["revenue"],
            r["ebitda"],
            r["net_profit"]
        ))
    return rows

# =========================
# STAGE 5: STORAGE LAYER
# =========================

def upsert_stock_master(conn, data):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO stock_master (symbol, company_name, sector, exchange)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (symbol)
            DO UPDATE SET company_name = EXCLUDED.company_name
            RETURNING stock_id
        """, (data["symbol"], data["company_name"], data["sector"], data["exchange"]))
        return cur.fetchone()[0]

def upsert_stock_metrics(conn, stock_id, data):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO stock_metrics (stock_id, pe_ratio, peg_ratio, last_updated)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (stock_id)
            DO UPDATE SET
                pe_ratio = EXCLUDED.pe_ratio,
                peg_ratio = EXCLUDED.peg_ratio,
                last_updated = EXCLUDED.last_updated
        """, (stock_id, data["pe_ratio"], data["peg_ratio"], datetime.now()))

def insert_quarterly_financials(conn, rows):
    with conn.cursor() as cur:
        execute_batch(cur, """
            INSERT INTO quarterly_financials
            (stock_id, financial_year, quarter, revenue, ebitda, net_profit)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (stock_id, financial_year, quarter)
            DO NOTHING
        """, rows)

# =========================
# INGESTION PIPELINE
# =========================

def ingest_stock(symbol):
    conn = get_db_connection()

    try:
        # -------- FETCH --------
        overview = fetch_api("OVERVIEW", symbol)
        if not overview or not validate_overview(overview):
            print(f"[SKIPPED] Invalid overview data for {symbol}")
            return

        income = fetch_api("INCOME_STATEMENT", symbol)
        if not income or "quarterlyReports" not in income:
            print(f"[SKIPPED] No quarterly data for {symbol}")
            return

        # -------- NORMALIZE --------
        normalized_overview = normalize_overview(overview)

        normalized_quarters = []
        for report in income["quarterlyReports"]:
            if validate_quarterly(report):
                normalized_quarters.append(normalize_quarterly(report))

        # -------- STORE --------
        stock_id = upsert_stock_master(conn, normalized_overview)
        upsert_stock_metrics(conn, stock_id, normalized_overview)

        quarterly_rows = transform_quarterly(stock_id, normalized_quarters)
        insert_quarterly_financials(conn, quarterly_rows)

        conn.commit()
        print(f"[SUCCESS] Ingested data for {symbol}")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] {symbol} | {e}")

    finally:
        conn.close()

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    symbols = ["AAPL", "MSFT"]  # example symbols
    for sym in symbols:
        ingest_stock(sym)
