from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid

from parser import parse_query_to_dsl
from validator import validate_dsl
from screener import build_where_clause
from database import (
    get_screening_data,
    get_connection,
    get_portfolio_holdings,
    sell_holding,
    simulate_market_prices
)

# -------------------------------------------------
# APP INIT
# -------------------------------------------------
app = FastAPI(title="AI Stock Screener")

# -------------------------------------------------
# SIMPLE AUTH (IN-MEMORY – DEMO SAFE)
# -------------------------------------------------
users_db = {}
token_store = {}

# -------------------------------------------------
# REQUEST MODELS
# -------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ScreenRequest(BaseModel):
    query: str


class AlertCreateRequest(BaseModel):
    query: str


class AddHoldingRequest(BaseModel):
    portfolio_id: int
    stock_id: int
    quantity: int
    buy_price: float


# -------------------------------------------------
# AUTH ROUTES
# -------------------------------------------------
@app.post("/register")
def register(data: RegisterRequest):
    users_db[data.username] = data.password
    return {"message": "registered"}


@app.post("/login")
def login(data: LoginRequest):
    if users_db.get(data.username) != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = str(uuid.uuid4())
    token_store[token] = data.username
    return {"token": token}


def require_auth(token: str):
    if token not in token_store:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token_store[token]


# -------------------------------------------------
# SCREENER
# -------------------------------------------------
@app.post("/screen")
def screen(data: ScreenRequest, token: str = Header(None)):
    require_auth(token)

    try:
        dsl = parse_query_to_dsl(data.query)
        validate_dsl(dsl)
        where_clause = build_where_clause(dsl)
        results = get_screening_data(where_clause)
        return {"count": len(results), "data": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------
# PORTFOLIO
# -------------------------------------------------
@app.post("/portfolio/create")
def create_portfolio(token: str = Header(None)):
    user_id = require_auth(token)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO portfolio (user_id, created_at) VALUES (?, ?)",
        (user_id, datetime.now().isoformat())
    )
    conn.commit()
    portfolio_id = cur.lastrowid
    conn.close()

    return {"portfolio_id": portfolio_id}


@app.post("/portfolio/add")
def add_to_portfolio(data: AddHoldingRequest, token: str = Header(None)):
    require_auth(token)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO portfolio_holdings
        (portfolio_id, stock_id, quantity, buy_price, buy_time)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.portfolio_id,
        data.stock_id,
        data.quantity,
        data.buy_price,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return {"message": "Stock added to portfolio"}


@app.get("/portfolio/{portfolio_id}")
def view_portfolio(portfolio_id: int, token: str = Header(None)):
    require_auth(token)
    return get_portfolio_holdings(portfolio_id)


@app.delete("/portfolio/sell/{holding_id}")
def sell_stock(holding_id: int, token: str = Header(None)):
    require_auth(token)
    sell_holding(holding_id)
    return {"message": "Stock sold"}


# -------------------------------------------------
# ALERTS
# -------------------------------------------------
@app.post("/alerts/create")
def create_alert(data: AlertCreateRequest, token: str = Header(None)):
    user_id = require_auth(token)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO alerts (user_id, query, created_at)
        VALUES (?, ?, ?)
    """, (user_id, data.query, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return {"message": "Alert created"}


@app.get("/alerts/check")
def check_alerts(token: str = Header(None)):
    user_id = require_auth(token)

    conn = get_connection()
    cur = conn.cursor()

    triggered = []

    cur.execute("SELECT id, query FROM alerts WHERE user_id = ?", (user_id,))
    alerts = cur.fetchall()

    for alert_id, query in alerts:
        try:
            dsl = parse_query_to_dsl(query)
            where_clause = build_where_clause(dsl)
            stocks = get_screening_data(where_clause)

            for s in stocks:
                cur.execute("""
                    INSERT OR IGNORE INTO alert_triggers
                    (alert_id, stock_id, triggered_at)
                    VALUES (?, ?, ?)
                """, (alert_id, s["stock_id"], datetime.now().isoformat()))

                if cur.rowcount > 0:
                    triggered.append({
                        "alert_id": alert_id,
                        "symbol": s["symbol"],
                        "company": s["company"],
                        "triggered_at": datetime.now().isoformat()
                    })

        except Exception:
            continue

    conn.commit()
    conn.close()

    return {"triggered_alerts": triggered}


# -------------------------------------------------
# MARKET SIMULATION
# -------------------------------------------------
@app.post("/simulate")
def simulate_market(token: str = Header(None)):
    require_auth(token)
    simulate_market_prices()
    return {"message": "Market prices updated"}
