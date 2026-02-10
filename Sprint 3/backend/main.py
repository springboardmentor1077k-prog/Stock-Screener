from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import operator

# --- IMPORTS FOR LOGIC ---
from llm_service import nl_to_dsl
from recursive_compiler import compile_dsl_to_sql_with_params

# ================= CONFIG =================
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

# =========================================
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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
    sector_summary: dict
    avg_pe: float
    avg_peg: float
    avg_dividend: float

class AlertCreate(BaseModel):
    metric: str      # e.g. "pe_ratio", "price"
    operator: str    # ">", "<"
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
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_analyst_rating(upside_pct):
    if upside_pct is None: return "N/A"
    if upside_pct >= 15: return "Strong Buy 🟢"
    if upside_pct >= 5: return "Buy 🔵"
    if upside_pct >= -5: return "Hold 🟡"
    return "Sell 🔴"

# ================= CORE LOGIC: EVALUATION ENGINE =================
def evaluate_alerts_logic(user_id: int):
    """
    1. Fetches Active Alerts
    2. Fetches Real-Time Stock Data
    3. Evaluates Conditions
    4. Records Triggers (Once only logic)
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    triggered_count = 0

    try:
        # A. Fetch Active Alerts for User
        cur.execute("""
            SELECT alert_id, metric, operator, threshold 
            FROM alerts 
            WHERE user_id = %s AND status = 'active'
        """, (user_id,))
        active_alerts = cur.fetchall()

        if not active_alerts:
            return 0

        # B. Fetch All Stocks & Fundamentals
        # We join stocks, fundamentals, and analysis_target (for price)
        cur.execute("""
            SELECT 
                s.stock_id, s.ticker,
                f.pe_ratio, f.peg_ratio, f.dividend_yield,
                a.current_price
            FROM stocks s
            LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
            LEFT JOIN analysis_target a ON s.stock_id = a.stock_id
        """)
        market_data = cur.fetchall()

        # Helper for operator string to function mapping
        ops = {
            '>': operator.gt,
            '<': operator.lt,
            '>=': operator.ge,
            '<=': operator.le,
            '=': operator.eq
        }

        # C. Evaluation Pipeline
        for alert in active_alerts:
            metric_name = alert['metric']
            op_func = ops.get(alert['operator'])
            threshold = float(alert['threshold'])
            
            if not op_func: continue # Skip invalid operators

            for stock in market_data:
                # 1. Scope Resolution & Metric Fetching
                # Map "price" to "current_price" for convenience
                db_field = "current_price" if metric_name == "price" else metric_name
                
                val = stock.get(db_field)

                # 2. Skip if Metric is Missing (Exception handling)
                if val is None:
                    continue 

                val = float(val)

                # 3. Condition Evaluation
                if op_func(val, threshold):
                    
                    # 4. Trigger Decision (Trigger Once Logic)
                    # Check if this specific event already happened
                    check_sql = """
                        SELECT event_id FROM alert_events 
                        WHERE alert_id = %s AND stock_id = %s
                    """
                    cur.execute(check_sql, (alert['alert_id'], stock['stock_id']))
                    already_triggered = cur.fetchone()

                    if not already_triggered:
                        # 5. Record Event
                        insert_sql = """
                            INSERT INTO alert_events (user_id, alert_id, stock_id, triggered_value)
                            VALUES (%s, %s, %s, %s)
                        """
                        cur.execute(insert_sql, (
                            user_id, 
                            alert['alert_id'], 
                            stock['stock_id'], 
                            val
                        ))
                        triggered_count += 1

        conn.commit()
        return triggered_count

    except Exception as e:
        conn.rollback()
        print(f"Evaluation Error: {e}")
        return 0
    finally:
        cur.close()
        conn.close()

# ================= ENDPOINTS =================

@app.get("/health")
def health():
    try:
        conn = get_db()
        conn.close()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}

@app.post("/signup")
def signup(data: SignupRequest):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE email=%s", (data.email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="User already exists")
    cur.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (data.email, hash_password(data.password)))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "User registered successfully"}

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT user_id, password_hash FROM users WHERE email=%s", (form.username,))
    user = cur.fetchone()
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"user_id": user["user_id"], "email": form.username})
    cur.close()
    conn.close()
    return {"access_token": token, "token_type": "bearer"}

@app.post("/nl-query")
def process_query(payload: NLQueryRequest, current_user: dict = Depends(get_current_user)):
    # 1. Parsing
    try:
        dsl = nl_to_dsl(payload.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    # 2. Compiling
    try:
        where_clause, query_params = compile_dsl_to_sql_with_params(dsl)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Compiler Error: {str(e)}")

    # 3. SQL Execution
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
        cur.execute(sql, query_params)
        results = cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL Error: {str(e)}")
    
    # 4. Enrich Data
    enriched_results = []
    for row in results:
        # Check if analyst data is present (non-None)
        has_analyst_data = (
            row.get('current_price') is not None and 
            row.get('high_target_price') is not None and 
            row.get('low_target_price') is not None
        )

        if has_analyst_data:
            try:
                avg_target = (float(row['high_target_price']) + float(row['low_target_price'])) / 2
                current = float(row['current_price'])
                
                if current > 0:
                    upside = ((avg_target - current) / current) * 100
                    row['analyst_upside'] = round(upside, 2)
                    row['analyst_rating'] = get_analyst_rating(upside)
                    row['avg_target'] = round(avg_target, 2)
                else:
                    row['analyst_upside'] = None
                    row['analyst_rating'] = "N/A"
            except:
                row['analyst_upside'] = None
                row['analyst_rating'] = "N/A"
        else:
            row['analyst_upside'] = None
            row['analyst_rating'] = "N/A"
        
        enriched_results.append(row)

    # 5. Save History
    try:
        cur.execute("INSERT INTO query_history (user_id, nl_query, dsl) VALUES (%s, %s, %s)", 
                   (current_user["user_id"], payload.query, json.dumps(dsl)))
        conn.commit()
    except:
        pass # Don't fail query if logging fails
        
    cur.close()
    conn.close()

    return {"query": payload.query, "dsl": dsl, "results": enriched_results}

@app.get("/query-history")
def history(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT nl_query, dsl, created_at FROM query_history WHERE user_id=%s ORDER BY created_at DESC", (current_user["user_id"],))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"history": rows}

@app.post("/explain-results")
def explain_results(payload: ExplainRequest, current_user: dict = Depends(get_current_user)):
    insights = []
    if payload.avg_pe < 15:
        val_insight = "📉 **Undervalued:** Low PE (<15) suggests value territory."
    elif payload.avg_pe > 30:
        val_insight = "🚀 **High Growth:** High PE (>30) suggests growth expectations."
    else:
        val_insight = "⚖️ **Fair Value:** Moderate PE (15-30)."
    insights.append(val_insight)

    if payload.avg_dividend > 2.5:
        div_insight = "💰 **Income Generators:** Yield > 2.5% is good for income."
    else:
        div_insight = "🌱 **Growth Focused:** Lower yield, likely reinvesting profits."
    insights.append(div_insight)

    bullet_points = "\n".join([f"- {i}" for i in insights])
    explanation = f"### 📊 AI Market Analysis\n\n📌 **Dynamic Interpretation:**\n{bullet_points}"
    return {"explanation": explanation}

@app.get("/portfolio")
def get_portfolio(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT 
            p.portfolio_id, p.quantity, p.average_price AS buy_price,
            s.ticker, s.company_name, s.sector, a.current_price
        FROM portfolio p
        JOIN stocks s ON p.stock_id = s.stock_id
        LEFT JOIN analysis_target a ON p.stock_id = a.stock_id
        WHERE p.user_id = %s
        ORDER BY s.ticker
    """
    
    cur.execute(query, (current_user['user_id'],))
    holdings = cur.fetchall()
    
    portfolio_summary = {"total_value": 0.0, "total_profit_loss": 0.0, "holdings": []}

    for item in holdings:
        current_price = float(item['current_price']) if item['current_price'] else 0.0
        buy_price = float(item['buy_price'])
        quantity = item['quantity']
        
        current_value = current_price * quantity
        investment_value = buy_price * quantity
        profit_loss = current_value - investment_value
        
        profit_loss_pct = (profit_loss / investment_value) * 100 if investment_value > 0 else 0.0

        portfolio_summary["total_value"] += current_value
        portfolio_summary["total_profit_loss"] += profit_loss

        item.update({
            "current_price": round(current_price, 2),
            "current_value": round(current_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_pct": round(profit_loss_pct, 2)
        })
        portfolio_summary["holdings"].append(item)

    cur.close()
    conn.close()
    return portfolio_summary

@app.post("/alerts")
def create_alert(alert: AlertCreate, current_user: dict = Depends(get_current_user)):
    """Create a new monitoring rule."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO alerts (user_id, metric, operator, threshold)
            VALUES (%s, %s, %s, %s)
            RETURNING alert_id
        """, (current_user['user_id'], alert.metric, alert.operator, alert.threshold))
        alert_id = cur.fetchone()[0]
        conn.commit()
        return {"message": "Alert created", "alert_id": alert_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.get("/alerts")
def get_alerts(current_user: dict = Depends(get_current_user)):
    """Fetch all alerts and their trigger history."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get Alerts
    cur.execute("SELECT * FROM alerts WHERE user_id = %s ORDER BY created_at DESC", (current_user['user_id'],))
    alerts = cur.fetchall()
    
    # Get Events (Triggers)
    cur.execute("""
        SELECT e.triggered_value, e.triggered_at, s.ticker, a.metric, a.operator, a.threshold
        FROM alert_events e
        JOIN stocks s ON e.stock_id = s.stock_id
        JOIN alerts a ON e.alert_id = a.alert_id
        WHERE e.user_id = %s
        ORDER BY e.triggered_at DESC
    """, (current_user['user_id'],))
    events = cur.fetchall()
    
    cur.close()
    conn.close()
    return {"alerts": alerts, "events": events}

@app.post("/alerts/check")
def run_alert_check(current_user: dict = Depends(get_current_user)):
    """Manually trigger the evaluation pipeline."""
    new_triggers = evaluate_alerts_logic(current_user['user_id'])
    return {"status": "success", "new_events_triggered": new_triggers}
