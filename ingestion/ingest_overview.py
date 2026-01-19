import requests, mysql.connector, os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
SYMBOL = "IBM"

data = requests.get(
    f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={SYMBOL}&apikey={API_KEY}"
).json()

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cur = db.cursor()

cur.execute("""
INSERT INTO stocks (symbol, company_name, sector, industry, exchange)
VALUES (%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
company_name=VALUES(company_name)
""", (
    SYMBOL,
    data.get("Name"),
    data.get("Sector"),
    data.get("Industry"),
    data.get("Exchange")
))

cur.execute("SELECT stock_id FROM stocks WHERE symbol=%s", (SYMBOL,))
stock_id = cur.fetchone()[0]

cur.execute("""
INSERT INTO fundamentals
(stock_id, pe_ratio, eps, market_cap, roe, debt_equity, updated_at)
VALUES (%s,%s,%s,%s,%s,%s,NOW())
ON DUPLICATE KEY UPDATE
pe_ratio=VALUES(pe_ratio),
eps=VALUES(eps),
market_cap=VALUES(market_cap),
roe=VALUES(roe),
debt_equity=VALUES(debt_equity),
updated_at=NOW()
""", (
    stock_id,
    float(data["PERatio"]) if data.get("PERatio") not in ("None", None) else None,
    float(data["EPS"]) if data.get("EPS") not in ("None", None) else None,
    int(data["MarketCapitalization"]) if data.get("MarketCapitalization") not in ("None", None) else None,
    float(data["ReturnOnEquityTTM"]) if data.get("ReturnOnEquityTTM") not in ("None", None) else None,
    float(data["DebtToEquity"]) if data.get("DebtToEquity") not in ("None", None) else None
))

db.commit()
cur.close()
db.close()
print("✅ Stock data ingested")
