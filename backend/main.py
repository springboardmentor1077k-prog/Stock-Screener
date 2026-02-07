from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uuid
from datetime import datetime

from parser import parse_query_to_dsl
from validator import validate_dsl
from screener import build_where_clause
from database import get_screening_data, get_connection

# -------------------------
# APP INIT
# -------------------------
app = FastAPI()

# -------------------------
# SIMPLE AUTH (IN-MEMORY)
# -------------------------
users_db = {}
token_store = {}

# -------------------------
# REQUEST MODELS
# -------------------------
class AuthRequest(BaseModel):
    username: str
    password: str

class ScreenRequest(BaseModel):
    query: str

# -------------------------
# AUTH ROUTES
# -------------------------
@app.post("/register")
def register(data: AuthRequest):
    users_db[data.username] = data.password
    return {"message": "registered"}

@app.post("/login")
def login(data: AuthRequest):
    if users_db.get(data.username) != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = str(uuid.uuid4())
    token_store[token] = data.username
    return {"token": token}

# -------------------------
# SNAPSHOT SCREENER
# -------------------------
@app.post("/screen")
def screen(data: ScreenRequest, token: str = Header(None)):
    if token not in token_store:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        dsl = parse_query_to_dsl(data.query)
        validate_dsl(dsl)

        where_clause = build_where_clause(dsl)
        results = get_screening_data(where_clause)

        return {
            "count": len(results),
            "data": results
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------
# CREATE ALERT
# -------------------------
@app.post("/alerts/create")
def create_alert(data: ScreenRequest, token: str = Header(None)):
    if token not in token_store:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # validate query
        dsl = parse_query_to_dsl(data.query)
        validate_dsl(dsl)

        user = token_store[token]
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO alerts (user_id, query, created_at)
            VALUES (?, ?, ?)
        """, (user, data.query, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

        return {"message": "Alert created"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# EVALUATE ALERTS (TRIGGER ONCE)
# -------------------------
@app.get("/alerts/evaluate")
def evaluate_alerts(token: str = Header(None)):
    if token not in token_store:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = token_store[token]
    conn = get_connection()
    cur = conn.cursor()

    try:
        # fetch user alerts
        cur.execute("""
            SELECT id, query
            FROM alerts
            WHERE user_id = ?
        """, (user,))
        alerts = cur.fetchall()

        triggered_events = []

        for alert_id, query in alerts:
            dsl = parse_query_to_dsl(query)
            where_clause = build_where_clause(dsl)
            stocks = get_screening_data(where_clause)

            for stock in stocks:
                stock_id = stock["stock_id"]

                # check if already triggered
                cur.execute("""
                    SELECT 1 FROM alert_triggers
                    WHERE alert_id = ? AND stock_id = ?
                """, (alert_id, stock_id))

                if cur.fetchone():
                    continue

                # record trigger
                cur.execute("""
                    INSERT INTO alert_triggers
                    (alert_id, stock_id, triggered_at)
                    VALUES (?, ?, ?)
                """, (alert_id, stock_id, datetime.utcnow().isoformat()))

                triggered_events.append({
                    "alert_id": alert_id,
                    "symbol": stock["symbol"],
                    "company": stock["company"],
                    "triggered_at": datetime.utcnow().isoformat()
                })

        conn.commit()
        conn.close()

        return {"triggered_alerts": triggered_events}

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
