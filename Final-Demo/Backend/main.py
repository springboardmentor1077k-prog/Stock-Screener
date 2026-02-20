from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from decimal import Decimal  # Required for Redis JSON serialization
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import operator
import hashlib
import redis
import logging
from contextlib import asynccontextmanager

# --- IMPORTS FOR LOGIC ---
from scheduler import start_scheduler  # Import the scheduler we created
from llm_service import nl_to_dsl, generate_market_insight
from recursive_compiler import compile_dsl_to_sql_with_params
from compliance import get_disclaimer, check_compliance, standardize_error

# ================= CONFIG =================
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
CACHE_TTL = 300  # 5 Minutes

DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

# --- REDIS CONFIG (Safe Connection) ---
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("✅ Redis Connected")
except Exception as e:
    print(f"⚠️ Redis Connection Failed (Running in Safe Mode): {e}")
    redis_client = None

# --- HELPER: JSON SERIALIZER ---
def json_serial(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# ================= APP SETUP WITH LIFESPAN =================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background scheduler
    start_scheduler()
    yield
    # Shutdown: Clean up if needed (scheduler shuts down automatically)

app = FastAPI(title="ProTrade AI Backend", lifespan=lifespan)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ================= CENTRALIZED EXCEPTION HANDLERS =================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"🔴 CRITICAL SERVER ERROR: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "Something went wrong. Please try again later."}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Request Failed", "message": exc.detail}
    )

# ================= DB UTILS =================
def get_db():
    try:
        return psycopg2.connect(**DATABASE_CONFIG)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Connection Failed: {str(e)}")

# ================= MODELS =================
class SignupRequest(BaseModel):
    email: str
    password: str

class NLQueryRequest(BaseModel):
    query: str

class ExplainRequest(BaseModel):
    stocks: list

class AlertCreate(BaseModel):
    metric: str
    operator: str
    threshold: float

# ================= AUTH UTILS ==================
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")

def get_analyst_rating(upside_pct):
    if upside_pct is None: return "N/A"
    if upside_pct >= 15: return "Strong Buy 🟢"
    if upside_pct >= 5: return "Buy 🔵"
    if upside_pct >= -5: return "Hold 🟡"
    return "Sell 🔴"

# ================= ENDPOINTS =================

@app.get("/health")
def health():
    return {"status": "ok", "redis": "connected" if redis_client else "offline"}

@app.post("/signup")
def signup(data: SignupRequest):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM users WHERE email=%s", (data.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="User already exists")
        cur.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (data.email, hash_password(data.password)))
        conn.commit()
        return {"message": "User registered successfully"}
    finally:
        cur.close()
        conn.close()

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT user_id, password_hash FROM users WHERE email=%s", (form.username,))
        user = cur.fetchone()
        if not user or not verify_password(form.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token({"user_id": user["user_id"], "email": form.username})
        return {"access_token": token, "token_type": "bearer"}
    finally:
        cur.close()
        conn.close()

@app.post("/screen") 
def process_query(payload: NLQueryRequest, current_user: dict = Depends(get_current_user)):
    # 1. Compliance
    if not check_compliance(payload.query):
        raise HTTPException(status_code=400, detail="I cannot answer queries regarding specific financial advice.")

    # 2. Redis Cache
    query_hash = hashlib.md5(payload.query.encode()).hexdigest()
    cache_key = f"query:{query_hash}"
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached: return json.loads(cached)
        except: pass

    # 3. Core Logic
    try:
        dsl = nl_to_dsl(payload.query)
        where_clause, params = compile_dsl_to_sql_with_params(dsl)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query Error: {str(e)}")

    sql = f"""
        SELECT 
            s.stock_id, s.ticker, s.company_name, s.sector, 
            f.pe_ratio, f.peg_ratio, f.dividend_yield, f.debt_to_equity,
            a.current_price, a.high_target_price, a.low_target_price
        FROM stocks s
        JOIN fundamentals f ON s.stock_id = f.stock_id
        LEFT JOIN analysis_target a ON s.stock_id = a.stock_id
        WHERE {where_clause}
        ORDER BY s.company_name
    """
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(sql, params)
        results = cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
    finally:
        cur.close()
        conn.close()
    
    # 4. Enrich Data
    enriched = []
    for row in results:
        upside = None
        rating = "N/A"
        if row.get('current_price') and row.get('high_target_price') and row.get('low_target_price'):
            try:
                avg = (float(row['high_target_price']) + float(row['low_target_price'])) / 2
                curr = float(row['current_price'])
                if curr > 0:
                    upside = ((avg - curr) / curr) * 100
                    rating = get_analyst_rating(upside)
            except: pass
        row['analyst_upside'] = round(upside, 2) if upside else None
        row['analyst_rating'] = rating
        enriched.append(row)

    response = {"query": payload.query, "results": enriched, "disclaimer": get_disclaimer("screener_results")}
    
    if redis_client:
        try:
            redis_client.setex(cache_key, CACHE_TTL, json.dumps(response, default=json_serial))
        except: pass

    return response

@app.post("/explain-results")
def explain_results(payload: ExplainRequest, current_user: dict = Depends(get_current_user)):
    insight = generate_market_insight(payload.stocks)
    return {"explanation": insight}

@app.get("/portfolio")
def get_portfolio(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT p.quantity, p.average_price AS buy_price, s.ticker, s.company_name, s.sector, a.current_price
            FROM portfolio p JOIN stocks s ON p.stock_id = s.stock_id LEFT JOIN analysis_target a ON p.stock_id = a.stock_id
            WHERE p.user_id = %s ORDER BY s.ticker
        """, (current_user['user_id'],))
        holdings = cur.fetchall()
        
        summary = {"total_value": 0.0, "total_profit_loss": 0.0, "holdings": []}
        for item in holdings:
            curr_price = float(item['current_price'] or 0)
            buy_price = float(item['buy_price'])
            qty = item['quantity']
            val = curr_price * qty
            pl = val - (buy_price * qty)
            pl_pct = (pl / (buy_price * qty)) * 100 if buy_price > 0 else 0
            
            summary["total_value"] += val
            summary["total_profit_loss"] += pl
            item.update({"current_value": val, "profit_loss": pl, "profit_loss_pct": pl_pct})
            summary["holdings"].append(item)
            
        return summary
    finally:
        cur.close()
        conn.close()

# --- ALERT ENDPOINTS ---

@app.post("/alerts")
def create_alert(alert: AlertCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    try:
        # Check duplicate
        cur.execute("SELECT alert_id FROM alerts WHERE user_id=%s AND metric=%s AND operator=%s AND threshold=%s", 
                    (current_user['user_id'], alert.metric, alert.operator, alert.threshold))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Alert already exists")
            
        cur.execute("INSERT INTO alerts (user_id, metric, operator, threshold) VALUES (%s, %s, %s, %s) RETURNING alert_id",
                    (current_user['user_id'], alert.metric, alert.operator, alert.threshold))
        aid = cur.fetchone()[0]
        conn.commit()
        return {"message": "Alert created", "alert_id": aid}
    finally:
        cur.close()
        conn.close()

@app.get("/alerts")
def get_alerts(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM alerts WHERE user_id = %s ORDER BY created_at DESC", (current_user['user_id'],))
        alerts = cur.fetchall()
        return {"alerts": alerts}
    finally:
        cur.close()
        conn.close()

# --- NEW: NOTIFICATION ENDPOINT ---
@app.get("/notifications")
def get_notifications(current_user: dict = Depends(get_current_user)):
    """Fetch recent triggered alerts for the user"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Get triggered events from the last 24 hours (or limit 10)
        cur.execute("""
            SELECT e.event_id, s.ticker, e.triggered_value, e.triggered_at, a.metric, a.operator, a.threshold
            FROM alert_events e
            JOIN stocks s ON e.stock_id = s.stock_id
            JOIN alerts a ON e.alert_id = a.alert_id
            WHERE e.user_id = %s
            ORDER BY e.triggered_at DESC LIMIT 5
        """, (current_user['user_id'],))
        events = cur.fetchall()
        return events
    finally:
        cur.close()
        conn.close()
