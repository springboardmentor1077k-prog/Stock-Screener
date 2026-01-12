import requests
import psycopg2
from datetime import datetime

API_KEY = "G7Q1ID8B79L1N84T"
SYMBOL = "GOOGL"

# Fetch company overview
url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={SYMBOL}&apikey={API_KEY}"
response = requests.get(url)
print("STATUS CODE:", response.status_code)
print("RAW TEXT:", response.text)

try:
    data = response.json() if response.text else {}
except ValueError:
    data = {}


# Check if API returned valid data
if not data.get("Symbol"):
    print("❌ Error: API returned empty or invalid response. Check API key and symbol.")
    exit(1)

# DB connection
conn = psycopg2.connect(
    dbname="stock_screener",
    user="postgres",
    password="aarya",
    host="localhost",
    port="5434"
)
cur = conn.cursor()
print("RAW API RESPONSE:", data)

# Insert into STOCK table
cur.execute("""
INSERT INTO stocks (stock_id, company_name, sector)
VALUES (%s, %s, %s)
ON CONFLICT (stock_id) DO NOTHING;
""", (
    int(data.get("CIK", 0)) if data.get("CIK") else None,
    data.get("Name"),
    data.get("Sector")
))

# Insert into FUNDAMENTALS table
last_updated = None
if data.get("LatestQuarter"):
    try:
        last_updated = datetime.strptime(data["LatestQuarter"], "%Y-%m-%d")
    except (ValueError, KeyError):
        last_updated = None

cur.execute("""
INSERT INTO fundamentals (stock_id, pe_ratio, peg_ratio, last_updated)
VALUES (%s, %s, %s, %s)
ON CONFLICT (stock_id) DO NOTHING;
""", (
    int(data.get("CIK", 0)) if data.get("CIK") else None,
    float(data["PERatio"]) if data.get("PERatio") and data["PERatio"] != "None" else None,
    float(data["PEGRatio"]) if data.get("PEGRatio") and data["PEGRatio"] != "None" else None,
    last_updated
))


try:
    conn.commit()
    print("✅ Stock & fundamentals data inserted successfully")
except psycopg2.Error as e:
    conn.rollback()
    print(f"❌ Database error: {e}")
finally:
    cur.close()
    conn.close()
