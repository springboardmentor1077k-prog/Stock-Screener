from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uuid
from datetime import datetime

from database import (
    get_screening_data,
    get_portfolio_holdings,
    simulate_market_prices,
    get_connection
)
from parser import parse_query_to_dsl
from validator import validate_dsl
from screener import build_where_clause

app = FastAPI()

users_db = {}
token_store = {}

class ScreenRequest(BaseModel):
    query: str

class AddHolding(BaseModel):
    portfolio_id: int
    stock_id: int
    quantity: int
    buy_price: float

@app.post("/register")
def register(data: dict):
    users_db[data["username"]] = data["password"]
    return {"message": "registered"}

@app.post("/login")
def login(data: dict):
    if users_db.get(data["username"]) != data["password"]:
        raise HTTPException(401, "Invalid credentials")
    token = str(uuid.uuid4())
    token_store[token] = data["username"]
    return {"token": token}

@app.post("/screen")
def screen(data: ScreenRequest, token: str = Header(None)):
    dsl = parse_query_to_dsl(data.query)
    validate_dsl(dsl)
    where_clause = build_where_clause(dsl)
    return {"data": get_screening_data(where_clause)}

@app.post("/portfolio/create")
def create_portfolio(token: str = Header(None)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO portfolio VALUES (NULL, ?, ?)", (token_store[token], datetime.utcnow().isoformat()))
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return {"portfolio_id": pid}

@app.post("/portfolio/add")
def add_holding(data: AddHolding, token: str = Header(None)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO portfolio_holdings VALUES (NULL,?,?,?,?)",
        (data.portfolio_id, data.stock_id, data.quantity, data.buy_price)
    )
    conn.commit()
    conn.close()
    return {"message": "added"}

@app.get("/portfolio/view/{pid}")
def view_portfolio(pid: int, token: str = Header(None)):
    return {"holdings": get_portfolio_holdings(pid)}

@app.post("/market/simulate")
def simulate_market(token: str = Header(None)):
    simulate_market_prices()
    return {"message": "market updated"}
