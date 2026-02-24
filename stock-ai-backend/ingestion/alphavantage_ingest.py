import requests
import time
import mysql.connector
from itertools import cycle
from collections import defaultdict

print("Script started")

# =========================
# CONFIG
# =========================

API_KEYS = [
    "FFVFDC6H7G38KO7C",
    "I8FH1CTTR3URL5XL"
]

BASE_URL = "https://www.alphavantage.co/query"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Sohan@2004",
    "database": "stock_screener"
}

MAX_SYMBOLS = 200

# =========================
# API KEY ROTATION
# =========================

api_key_cycle = cycle(API_KEYS)
key_usage = defaultdict(list)

def get_available_key():
    while True:
        key = next(api_key_cycle)
        now = time.time()

        key_usage[key] = [t for t in key_usage[key] if now - t < 60]

        if len(key_usage[key]) < 5:
            key_usage[key].append(now)
            return key

        time.sleep(1)

# =========================
# DB CONNECTION
# =========================

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# =========================
# CHECK IF STOCK EXISTS
# =========================

def stock_exists(symbol):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM stocks_master WHERE symbol=%s", (symbol,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# =========================
# FETCH SYMBOLS
# =========================

def fetch_200_symbols():
    params = {
        "function": "LISTING_STATUS",
        "apikey": API_KEYS[0]
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    text_data = response.text.strip()

    if text_data.startswith("{"):
        print("⚠️ LISTING_STATUS throttled:")
        print(text_data)
        return []

    rows = text_data.split("\n")
    symbols = []

    for row in rows[1:]:
        parts = row.split(",")
        if len(parts) > 6:
            symbol = parts[0].strip()
            asset_type = parts[3].strip()
            status = parts[-1].strip()

            if symbol and asset_type == "Stock" and status == "Active":
                symbols.append(symbol)

        if len(symbols) >= MAX_SYMBOLS:
            break

    print(f"Fetched {len(symbols)} symbols")
    return symbols

# =========================
# FETCH API
# =========================

def fetch_alpha_vantage(function, symbol):
    api_key = get_available_key()

    params = {
        "function": function,
        "symbol": symbol,
        "apikey": api_key
    }

    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "Note" in data or "Information" in data:
        print("⚠️ Throttled. Sleeping 60s...")
        time.sleep(60)
        return fetch_alpha_vantage(function, symbol)

    if "Error Message" in data:
        raise RuntimeError(f"API error for {symbol}")

    return data

# =========================
# HELPERS
# =========================

def safe_float(val):
    try:
        return float(val)
    except:
        return None

# =========================
# INGEST STOCK
# =========================

def ingest_stock(symbol):

    if stock_exists(symbol):
        print(f"⏭ Skipping {symbol}")
        return

    print(f"🔄 Ingesting {symbol}")

    overview = fetch_alpha_vantage("OVERVIEW", symbol)

    if not overview or "Name" not in overview:
        print(f"⚠️ Skipping {symbol} (Invalid overview)")
        return

    cashflow = fetch_alpha_vantage("CASH_FLOW", symbol)
    quote = fetch_alpha_vantage("GLOBAL_QUOTE", symbol)

    conn = get_db()
    cursor = conn.cursor()

    # Insert into stocks_master
    cursor.execute("""
        INSERT INTO stocks_master (symbol, company_name, sector, exchange)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            company_name = VALUES(company_name),
            sector = VALUES(sector),
            exchange = VALUES(exchange)
    """, (
        symbol,
        overview.get("Name"),
        overview.get("Sector"),
        overview.get("Exchange")
    ))

    conn.commit()

    cursor.execute("SELECT id FROM stocks_master WHERE symbol=%s", (symbol,))
    stock_id = cursor.fetchone()[0]

    # Fundamentals
    operating_cf = safe_float(
        cashflow.get("annualReports", [{}])[0].get("operatingCashflow")
    )
    capex = safe_float(
        cashflow.get("annualReports", [{}])[0].get("capitalExpenditures")
    )

    free_cash_flow = (
        operating_cf - abs(capex)
        if operating_cf is not None and capex is not None
        else None
    )

    debt = safe_float(
        overview.get("TotalDebt") or overview.get("ShortTermDebt")
    )

    cursor.execute("""
        INSERT INTO fundamentals
        (stock_id, pe_ratio, peg_ratio, debt, free_cash_flow, last_updated)
        VALUES (%s, %s, %s, %s, %s, CURDATE())
        ON DUPLICATE KEY UPDATE
            pe_ratio = VALUES(pe_ratio),
            peg_ratio = VALUES(peg_ratio),
            debt = VALUES(debt),
            free_cash_flow = VALUES(free_cash_flow),
            last_updated = CURDATE()
    """, (
        stock_id,
        safe_float(overview.get("PERatio")),
        safe_float(overview.get("PEGRatio")),
        debt,
        free_cash_flow
    ))

    # Analyst Targets
    current_price = None
    if quote and "Global Quote" in quote:
        current_price = safe_float(
            quote["Global Quote"].get("05. price")
        )

    target_low = safe_float(overview.get("52WeekLow"))
    target_high = safe_float(overview.get("52WeekHigh"))

    cursor.execute("""
        INSERT INTO analyst_targets
        (stock_id, target_price_low, target_price_high, current_market_price, last_updated)
        VALUES (%s, %s, %s, %s, CURDATE())
        ON DUPLICATE KEY UPDATE
            target_price_low = VALUES(target_price_low),
            target_price_high = VALUES(target_price_high),
            current_market_price = VALUES(current_market_price),
            last_updated = CURDATE()
    """, (
        stock_id,
        target_low,
        target_high,
        current_price
    ))

    conn.commit()
    conn.close()

    print(f"✅ Completed {symbol}")

    time.sleep(2)

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print("Inside main")

    symbols = fetch_200_symbols()

    if not symbols:
        print("No symbols returned.")
    else:
        for sym in symbols:
            try:
                ingest_stock(sym)
            except Exception as e:
                print(f"❌ Failed for {sym}: {e}")
