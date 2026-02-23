from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import uuid
import redis
import json
import hashlib

from parser import parse_query_to_dsl
from validator import validate_dsl
from screener import build_where_clause
from alerts import evaluate_alerts, list_alert_status

from database import (
    get_screening_data,
    get_connection,
    get_portfolio_holdings,
    sell_holding,
    simulate_market_prices
)

app = FastAPI(title="AI Stock Explorer")

try:
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"System error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "SYSTEM_ERROR",
            "message": "Temporary system issue. Please try again later."
        }
    )


users_db = {}
token_store = {}

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ScreenRequest(BaseModel):
    query: str

class AddHoldingRequest(BaseModel):
    portfolio_id: int
    stock_id: int
    quantity: int
    buy_price: float

class AlertRequest(BaseModel):
    query: str


def require_auth(token: str):
    if token not in token_store:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token_store[token]


def safe_redis_get(key):
    if not REDIS_AVAILABLE:
        return None
    try:
        return redis_client.get(key)
    except Exception:
        return None


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


@app.post("/screen")
def screen(data: ScreenRequest, token: str = Header(None)):
    require_auth(token)

    dsl = parse_query_to_dsl(data.query)
    validate_dsl(dsl)
    where_clause = build_where_clause(dsl)

    results = None

    if REDIS_AVAILABLE:
        raw_key = f"screen:{where_clause}"
        cache_key = hashlib.md5(raw_key.encode()).hexdigest()

        cached = safe_redis_get(cache_key)
        if cached:
            results = json.loads(cached)
        else:
            results = get_screening_data(where_clause)
            redis_client.setex(cache_key, 60, json.dumps(results))
    else:
        results = get_screening_data(where_clause)

    if not results:
        return {"count": 0, "data": [], "message": "No matching results"}

    return {"count": len(results), "data": results}


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
    pid = cur.lastrowid
    conn.close()

    return {"portfolio_id": pid}


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

    return {"message": "added"}


@app.get("/portfolio/{portfolio_id}")
def view_portfolio(portfolio_id: int, token: str = Header(None)):
    require_auth(token)
    return get_portfolio_holdings(portfolio_id)


@app.delete("/portfolio/sell/{holding_id}")
def sell_stock(holding_id: int, token: str = Header(None)):
    require_auth(token)
    sell_holding(holding_id)
    return {"message": "sold"}


@app.post("/simulate")
def simulate_market(token: str = Header(None)):

    user = require_auth(token)

    simulate_market_prices()
    evaluate_alerts(user)

    if REDIS_AVAILABLE:
        try:
            redis_client.flushdb()
        except Exception:
            pass

    return {"message": "market updated"}


@app.post("/alerts/create")
def create_alert(data: AlertRequest, token: str = Header(None)):
    username = require_auth(token)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO alerts (user_id, query, created_at)
        VALUES (?, ?, ?)
    """, (
        username,
        data.query,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return {"message": "alert created"}


@app.get("/alerts/check")
def check_alerts(token: str = Header(None)):
    username = require_auth(token)
    triggered = evaluate_alerts(username)
    return {"triggered_alerts": triggered}


@app.get("/alerts/status")
def alerts_status(token: str = Header(None)):
    username = require_auth(token)
    return list_alert_status(username)
