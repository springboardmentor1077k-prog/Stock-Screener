import os
import sys
import sqlite3
import secrets
from datetime import datetime
from flask import Flask, request, jsonify
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.nlp.nl_query_engine import NLQueryEngine
from werkzeug.security import generate_password_hash, check_password_hash


DB_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DB_DIR / "quantdash.db"


def ensure_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stocks(
            symbol TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            sector TEXT,
            price REAL,
            market_cap_b REAL,
            pe_ratio REAL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolio_holdings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            shares REAL NOT NULL,
            cost_basis REAL NOT NULL,
            FOREIGN KEY(portfolio_id) REFERENCES portfolios(id),
            FOREIGN KEY(symbol) REFERENCES stocks(symbol)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            op TEXT NOT NULL,
            threshold REAL NOT NULL,
            created_at TEXT NOT NULL,
            fired_at TEXT,
            FOREIGN KEY(symbol) REFERENCES stocks(symbol)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alert_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            event_time TEXT NOT NULL,
            price REAL NOT NULL,
            direction TEXT NOT NULL,
            threshold REAL NOT NULL,
            FOREIGN KEY(alert_id) REFERENCES alerts(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analyst_ratings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            rating TEXT,
            rating_date TEXT,
            FOREIGN KEY(symbol) REFERENCES stocks(symbol)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            label TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, symbol),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(symbol) REFERENCES stocks(symbol)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            issued_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    seed_if_empty(conn)
    conn.close()


def seed_if_empty(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stocks")
    count = cur.fetchone()[0]
    if count < 100:
        rows = [
            ("AAPL", "Apple Inc.", "Technology", 185.0, 2900.0, 28.0),
            ("MSFT", "Microsoft Corp.", "Technology", 410.0, 3100.0, 35.0),
            ("GOOGL", "Alphabet Inc.", "Technology", 145.0, 1900.0, 26.0),
            ("META", "Meta Platforms Inc.", "Technology", 330.0, 850.0, 24.0),
            ("NVDA", "NVIDIA Corp.", "Technology", 720.0, 1800.0, 55.0),
            ("ORCL", "Oracle Corp.", "Technology", 115.0, 320.0, 26.0),
            ("IBM", "International Business Machines", "Technology", 165.0, 150.0, 18.0),
            ("INTC", "Intel Corp.", "Technology", 42.0, 170.0, 15.0),
            ("AMD", "Advanced Micro Devices", "Technology", 130.0, 210.0, 48.0),
            ("CRM", "Salesforce Inc.", "Technology", 280.0, 270.0, 32.0),
            ("ADBE", "Adobe Inc.", "Technology", 520.0, 240.0, 38.0),
            ("AVGO", "Broadcom Inc.", "Technology", 1280.0, 650.0, 28.0),
            ("CSCO", "Cisco Systems Inc.", "Technology", 56.0, 220.0, 17.0),
            ("TXN", "Texas Instruments Inc.", "Technology", 165.0, 150.0, 22.0),
            ("QCOM", "Qualcomm Inc.", "Technology", 155.0, 170.0, 20.0),
            ("SAP", "SAP SE", "Technology", 180.0, 220.0, 25.0),
            ("SHOP", "Shopify Inc.", "Technology", 85.0, 110.0, 60.0),
            ("SNOW", "Snowflake Inc.", "Technology", 200.0, 65.0, 58.0),
            ("NOW", "ServiceNow Inc.", "Technology", 740.0, 150.0, 42.0),
            ("MU", "Micron Technology Inc.", "Technology", 90.0, 100.0, 21.0),
            ("AMZN", "Amazon.com Inc.", "Consumer Discretionary", 155.0, 1600.0, 60.0),
            ("TSLA", "Tesla Inc.", "Consumer Discretionary", 190.0, 600.0, 55.0),
            ("HD", "Home Depot Inc.", "Consumer Discretionary", 360.0, 360.0, 23.0),
            ("LOW", "Lowe's Companies Inc.", "Consumer Discretionary", 220.0, 130.0, 21.0),
            ("COST", "Costco Wholesale Corp.", "Consumer Discretionary", 720.0, 320.0, 34.0),
            ("MCD", "McDonald's Corp.", "Consumer Discretionary", 290.0, 210.0, 28.0),
            ("SBUX", "Starbucks Corp.", "Consumer Discretionary", 94.0, 105.0, 27.0),
            ("NKE", "Nike Inc.", "Consumer Discretionary", 110.0, 170.0, 30.0),
            ("TGT", "Target Corp.", "Consumer Discretionary", 150.0, 70.0, 18.0),
            ("TJX", "TJX Companies Inc.", "Consumer Discretionary", 106.0, 120.0, 25.0),
            ("ROST", "Ross Stores Inc.", "Consumer Discretionary", 148.0, 50.0, 26.0),
            ("GM", "General Motors Co.", "Consumer Discretionary", 40.0, 55.0, 7.0),
            ("F", "Ford Motor Co.", "Consumer Discretionary", 12.0, 50.0, 6.0),
            ("BKNG", "Booking Holdings Inc.", "Consumer Discretionary", 3650.0, 130.0, 29.0),
            ("MAR", "Marriott International", "Consumer Discretionary", 220.0, 65.0, 24.0),
            ("YUM", "Yum! Brands Inc.", "Consumer Discretionary", 135.0, 38.0, 25.0),
            ("CMG", "Chipotle Mexican Grill", "Consumer Discretionary", 2750.0, 77.0, 58.0),
            ("EBAY", "eBay Inc.", "Consumer Discretionary", 48.0, 25.0, 15.0),
            ("ETSY", "Etsy Inc.", "Consumer Discretionary", 72.0, 9.0, 33.0),
            ("JPM", "JPMorgan Chase & Co.", "Financials", 178.0, 520.0, 11.0),
            ("BAC", "Bank of America Corp.", "Financials", 36.0, 290.0, 10.0),
            ("WFC", "Wells Fargo & Co.", "Financials", 52.0, 180.0, 9.0),
            ("C", "Citigroup Inc.", "Financials", 50.0, 95.0, 7.0),
            ("GS", "Goldman Sachs Group Inc.", "Financials", 395.0, 130.0, 11.0),
            ("MS", "Morgan Stanley", "Financials", 95.0, 160.0, 14.0),
            ("PNC", "PNC Financial Services", "Financials", 152.0, 65.0, 12.0),
            ("USB", "U.S. Bancorp", "Financials", 42.0, 65.0, 10.0),
            ("SCHW", "Charles Schwab Corp.", "Financials", 75.0, 130.0, 17.0),
            ("BK", "Bank of New York Mellon", "Financials", 56.0, 45.0, 12.0),
            ("AIG", "American International Group", "Financials", 70.0, 50.0, 9.0),
            ("PGR", "Progressive Corp.", "Financials", 190.0, 110.0, 18.0),
            ("AXP", "American Express Co.", "Financials", 220.0, 160.0, 19.0),
            ("COF", "Capital One Financial", "Financials", 130.0, 50.0, 8.0),
            ("BLK", "BlackRock Inc.", "Financials", 790.0, 120.0, 20.0),
            ("TROW", "T. Rowe Price Group", "Financials", 115.0, 25.0, 14.0),
            ("MET", "MetLife Inc.", "Financials", 70.0, 55.0, 8.0),
            ("PRU", "Prudential Financial Inc.", "Financials", 100.0, 36.0, 7.0),
            ("CME", "CME Group Inc.", "Financials", 225.0, 80.0, 25.0),
            ("ICE", "Intercontinental Exchange Inc.", "Financials", 140.0, 80.0, 24.0),
            ("XOM", "Exxon Mobil Corp.", "Energy", 105.0, 420.0, 9.0),
            ("CVX", "Chevron Corp.", "Energy", 150.0, 290.0, 10.0),
            ("COP", "ConocoPhillips", "Energy", 125.0, 150.0, 11.0),
            ("SLB", "Schlumberger Ltd.", "Energy", 54.0, 75.0, 18.0),
            ("EOG", "EOG Resources Inc.", "Energy", 130.0, 78.0, 10.0),
            ("PXD", "Pioneer Natural Resources", "Energy", 230.0, 55.0, 12.0),
            ("OXY", "Occidental Petroleum", "Energy", 62.0, 55.0, 12.0),
            ("KMI", "Kinder Morgan Inc.", "Energy", 18.0, 42.0, 15.0),
            ("MPC", "Marathon Petroleum", "Energy", 170.0, 75.0, 8.0),
            ("PSX", "Phillips 66", "Energy", 155.0, 68.0, 7.0),
            ("HAL", "Halliburton Co.", "Energy", 36.0, 31.0, 14.0),
            ("VLO", "Valero Energy Corp.", "Energy", 145.0, 54.0, 7.0),
            ("BKR", "Baker Hughes Co.", "Energy", 30.0, 32.0, 22.0),
            ("DVN", "Devon Energy Corp.", "Energy", 48.0, 31.0, 7.0),
            ("MRO", "Marathon Oil Corp.", "Energy", 26.0, 17.0, 8.0),
            ("APA", "APA Corp.", "Energy", 34.0, 11.0, 6.0),
            ("FANG", "Diamondback Energy Inc.", "Energy", 185.0, 33.0, 9.0),
            ("LNG", "Cheniere Energy Inc.", "Energy", 160.0, 40.0, 19.0),
            ("ENB", "Enbridge Inc.", "Energy", 35.0, 75.0, 16.0),
            ("WMB", "Williams Companies Inc.", "Energy", 39.0, 48.0, 18.0),
            ("JNJ", "Johnson & Johnson", "Health Care", 155.0, 380.0, 17.0),
            ("PFE", "Pfizer Inc.", "Health Care", 28.0, 160.0, 9.0),
            ("MRK", "Merck & Co. Inc.", "Health Care", 120.0, 300.0, 15.0),
            ("ABBV", "AbbVie Inc.", "Health Care", 165.0, 290.0, 14.0),
            ("UNH", "UnitedHealth Group Inc.", "Health Care", 520.0, 480.0, 24.0),
            ("TMO", "Thermo Fisher Scientific", "Health Care", 580.0, 230.0, 30.0),
            ("DHR", "Danaher Corp.", "Health Care", 250.0, 185.0, 28.0),
            ("MDT", "Medtronic plc", "Health Care", 88.0, 120.0, 20.0),
            ("ABT", "Abbott Laboratories", "Health Care", 110.0, 195.0, 24.0),
            ("BMY", "Bristol-Myers Squibb", "Health Care", 50.0, 100.0, 7.0),
            ("GILD", "Gilead Sciences Inc.", "Health Care", 76.0, 95.0, 12.0),
            ("AMGN", "Amgen Inc.", "Health Care", 310.0, 170.0, 19.0),
            ("ISRG", "Intuitive Surgical Inc.", "Health Care", 420.0, 150.0, 50.0),
            ("ZTS", "Zoetis Inc.", "Health Care", 180.0, 80.0, 33.0),
            ("HUM", "Humana Inc.", "Health Care", 360.0, 45.0, 18.0),
            ("CVS", "CVS Health Corp.", "Health Care", 70.0, 90.0, 11.0),
            ("CI", "Cigna Group", "Health Care", 340.0, 100.0, 17.0),
            ("SYK", "Stryker Corp.", "Health Care", 320.0, 120.0, 30.0),
            ("BIIB", "Biogen Inc.", "Health Care", 250.0, 36.0, 17.0),
            ("REGN", "Regeneron Pharmaceuticals", "Health Care", 1040.0, 120.0, 30.0),
        ]
        cur.executemany(
            "INSERT OR IGNORE INTO stocks(symbol, company_name, sector, price, market_cap_b, pe_ratio) VALUES(?,?,?,?,?,?)",
            rows,
        )
        conn.commit()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ok(items):
    return jsonify({"ok": True, "items": items, "count": len(items)})


def err(code, message, http=400):
    return jsonify({"ok": False, "code": code, "message": message}), http


app = Flask(__name__)
ensure_db()
engine = NLQueryEngine()

def current_user_id():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    cur = get_conn().cursor()
    row = cur.execute(
        "SELECT user_id FROM sessions WHERE token=?", (token,)
    ).fetchone()
    if not row:
        return None
    return row["user_id"]


@app.post("/api/v2/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or "@" not in email or len(password) < 6:
        return err("invalid_params", "valid email and password length >= 6 required", 400)
    conn = get_conn()
    cur = conn.cursor()
    existing = cur.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        return err("duplicate_user", "email already registered", 409)
    ph = generate_password_hash(password)
    ts = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO users(email, password_hash, created_at) VALUES(?,?,?)",
        (email, ph, ts),
    )
    conn.commit()
    uid = cur.lastrowid
    return ok([{"user_id": uid, "email": email}])


@app.post("/api/v2/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return err("invalid_params", "email and password required", 400)
    conn = get_conn()
    cur = conn.cursor()
    user = cur.execute(
        "SELECT id, password_hash FROM users WHERE email=?", (email,)
    ).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return err("auth_failed", "invalid credentials", 401)
    token = secrets.token_hex(16)
    ts = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO sessions(user_id, token, issued_at) VALUES(?,?,?)",
        (user["id"], token, ts),
    )
    conn.commit()
    return ok([{"user_id": user["id"], "email": email, "token": token}])


@app.post("/api/v2/screener")
def screener():
    if current_user_id() is None:
        return err("unauthorized", "valid token required", 401)
    data = request.get_json(silent=True) or {}
    query = data.get("query", "") or ""
    sector = data.get("sector")
    cur = get_conn().cursor()
    filters = []
    params = []
    if query.strip():
        try:
            parsed = engine.parse(query)
        except ValueError as e:
            return err("query_rejected", str(e), 400)
        if parsed.get("sector"):
            filters.append("LOWER(sector)=LOWER(?)")
            params.append(parsed["sector"])
        for rule in parsed.get("numerics", []):
            field = rule["field"]
            op = rule["op"]
            val = rule["value"]
            if field == "market_cap_b":
                filters.append(f"market_cap_b {op} ?")
                params.append(val)
            if field == "price":
                filters.append(f"price {op} ?")
                params.append(val)
            if field == "pe_ratio":
                filters.append(f"pe_ratio {op} ?")
                params.append(val)
    if sector:
        filters.append("LOWER(sector)=LOWER(?)")
        params.append(sector)
    sql = "SELECT symbol, company_name, sector, price, market_cap_b, pe_ratio FROM stocks"
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY market_cap_b DESC"
    rows = cur.execute(sql, params).fetchall()
    items = [dict(r) for r in rows]
    return ok(items)


@app.get("/api/v2/holdings")
def holdings():
    if current_user_id() is None:
        return err("unauthorized", "valid token required", 401)
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT ph.id as holding_id, p.name as portfolio, ph.symbol, s.company_name, s.sector,
               ph.shares, ph.cost_basis, s.price,
               (ph.shares * s.price) as current_value,
               ((s.price - ph.cost_basis) * ph.shares) as profit_loss
        FROM portfolio_holdings ph
        JOIN portfolios p ON p.id = ph.portfolio_id
        JOIN stocks s ON s.symbol = ph.symbol
        ORDER BY p.id, ph.id
        """
    ).fetchall()
    items = [dict(r) for r in rows]
    return ok(items)


@app.get("/api/v2/alerts")
def list_alerts():
    if current_user_id() is None:
        return err("unauthorized", "valid token required", 401)
    cur = get_conn().cursor()
    rows = cur.execute(
        """
        SELECT id, symbol, op, threshold, created_at, fired_at
        FROM alerts
        ORDER BY id DESC
        """
    ).fetchall()
    items = [dict(r) for r in rows]
    return ok(items)


def normalize_op(direction):
    d = (direction or "").strip().lower()
    if d in [">", ">", "above", "over", "greater", "greater than", "gt"]:
        return ">"
    if d in ["<", "<", "below", "under", "less", "less than", "lt"]:
        return "<"
    return None


@app.post("/api/v2/alerts")
def create_alert():
    if current_user_id() is None:
        return err("unauthorized", "valid token required", 401)
    data = request.get_json(silent=True) or {}
    symbol = data.get("symbol")
    direction = data.get("direction")
    threshold = data.get("threshold")
    op = normalize_op(direction)
    if not symbol or op is None or threshold is None:
        return err("invalid_params", "symbol, direction and threshold are required", 400)
    conn = get_conn()
    cur = conn.cursor()
    exists = cur.execute("SELECT 1 FROM stocks WHERE symbol=?", (symbol,)).fetchone()
    if not exists:
        return err("unknown_symbol", "symbol not found", 404)
    ts = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO alerts(symbol, op, threshold, created_at) VALUES(?,?,?,?)",
        (symbol, op, float(threshold), ts),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = cur.execute(
        "SELECT id, symbol, op, threshold, created_at, fired_at FROM alerts WHERE id=?",
        (new_id,),
    ).fetchone()
    return ok([dict(row)])


@app.post("/api/v2/alerts/run")
def run_alerts():
    if current_user_id() is None:
        return err("unauthorized", "valid token required", 401)
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, symbol, op, threshold, fired_at FROM alerts WHERE fired_at IS NULL"
    ).fetchall()
    to_fire = []
    for r in rows:
        sym = r["symbol"]
        op = r["op"]
        thr = r["threshold"]
        price_row = cur.execute("SELECT price FROM stocks WHERE symbol=?", (sym,)).fetchone()
        if not price_row:
            continue
        price = price_row["price"]
        cond = (price > thr) if op == ">" else (price < thr)
        if cond:
            to_fire.append((r["id"], sym, op, thr, price))
    fired_items = []
    for alert_id, sym, op, thr, price in to_fire:
        ts = datetime.utcnow().isoformat()
        cur.execute(
            "INSERT INTO alert_events(alert_id, symbol, event_time, price, direction, threshold) VALUES(?,?,?,?,?,?)",
            (alert_id, sym, ts, float(price), op, float(thr)),
        )
        cur.execute("UPDATE alerts SET fired_at=? WHERE id=?", (ts, alert_id))
        fired_items.append(
            {
                "alert_id": alert_id,
                "symbol": sym,
                "direction": op,
                "threshold": thr,
                "price": price,
                "event_time": ts,
            }
        )
    conn.commit()
    return ok(fired_items)


@app.get("/api/v2/favorites")
def list_favorites():
    uid = current_user_id()
    if uid is None:
        return err("unauthorized", "valid token required", 401)
    cur = get_conn().cursor()
    rows = cur.execute(
        """
        SELECT f.id as favorite_id, f.symbol, f.label, s.sector, s.price
        FROM favorites f
        JOIN stocks s ON s.symbol = f.symbol
        WHERE f.user_id=?
        ORDER BY f.id DESC
        """,
        (uid,),
    ).fetchall()
    items = [dict(r) for r in rows]
    return ok(items)


@app.post("/api/v2/favorites")
def add_favorite():
    uid = current_user_id()
    if uid is None:
        return err("unauthorized", "valid token required", 401)
    data = request.get_json(silent=True) or {}
    symbol = (data.get("symbol") or "").strip().upper()
    label = (data.get("label") or "").strip()
    if not symbol or not label:
        return err("invalid_params", "symbol and label are required", 400)
    conn = get_conn()
    cur = conn.cursor()
    exists = cur.execute("SELECT 1 FROM stocks WHERE symbol=?", (symbol,)).fetchone()
    if not exists:
        return err("unknown_symbol", "symbol not found", 404)
    ts = datetime.utcnow().isoformat()
    try:
        cur.execute(
            "INSERT INTO favorites(user_id, symbol, label, created_at) VALUES(?,?,?,?)",
            (uid, symbol, label, ts),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return err("duplicate_favorite", "already in favorites", 409)
    row = cur.execute(
        """
        SELECT f.id as favorite_id, f.symbol, f.label, s.sector, s.price
        FROM favorites f
        JOIN stocks s ON s.symbol=f.symbol
        WHERE f.id=?
        """,
        (cur.lastrowid,),
    ).fetchone()
    return ok([dict(row)])


@app.post("/api/v2/favorites/remove")
def remove_favorite():
    uid = current_user_id()
    if uid is None:
        return err("unauthorized", "valid token required", 401)
    data = request.get_json(silent=True) or {}
    fid = data.get("favorite_id")
    if not fid:
        return err("invalid_params", "favorite_id required", 400)
    conn = get_conn()
    cur = conn.cursor()
    own = cur.execute("SELECT id FROM favorites WHERE id=? AND user_id=?", (fid, uid)).fetchone()
    if not own:
        return err("not_found", "favorite not found", 404)
    cur.execute("DELETE FROM favorites WHERE id=?", (fid,))
    conn.commit()
    return ok([])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

