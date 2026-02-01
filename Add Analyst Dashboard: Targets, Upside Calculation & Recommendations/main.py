from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import json

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

# ================= DB =====================
def get_db():
    return psycopg2.connect(**DATABASE_CONFIG)

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

# ================= UTILS ==================
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
    """Helper to assign a rating based on upside potential"""
    if upside_pct is None: return "N/A"
    if upside_pct >= 15: return "Strong Buy 🟢"
    if upside_pct >= 5: return "Buy 🔵"
    if upside_pct >= -5: return "Hold 🟡"
    return "Sell 🔴"

# ================= HEALTH =================
@app.get("/health")
def health():
    try:
        conn = get_db()
        conn.close()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}

# ================= AUTH ===================
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

# ================= NL QUERY =================
@app.post("/nl-query")
def process_query(payload: NLQueryRequest, current_user: dict = Depends(get_current_user)):
    # 1. Parsing
    try:
        dsl = nl_to_dsl(payload.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing query: {str(e)}")

    # 2. Compiling
    try:
        where_clause, query_params = compile_dsl_to_sql_with_params(dsl)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error compiling DSL: {str(e)}")

    # 3. SQL Execution (With Analyst Joins)
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
    cur.execute(sql, query_params)
    results = cur.fetchall()

    # 4. Enrich Data
    enriched_results = []
    for row in results:
        if row['current_price'] and row['high_target_price'] and row['low_target_price']:
            try:
                avg_target = (float(row['high_target_price']) + float(row['low_target_price'])) / 2
                current = float(row['current_price'])
                if current > 0:
                    upside = ((avg_target - current) / current) * 100
                    row['analyst_upside'] = round(upside, 2)
                    row['analyst_rating'] = get_analyst_rating(upside)
                    row['avg_target'] = round(avg_target, 2)
                else:
                    raise ValueError
            except:
                row['analyst_upside'] = None
                row['analyst_rating'] = "N/A"
        else:
            row['analyst_upside'] = None
            row['analyst_rating'] = "N/A"
        
        enriched_results.append(row)

    # 5. Save History
    cur.execute("INSERT INTO query_history (user_id, nl_query, dsl) VALUES (%s, %s, %s)", 
               (current_user["user_id"], payload.query, json.dumps(dsl)))
    conn.commit()
    cur.close()
    conn.close()

    return {"query": payload.query, "dsl": dsl, "results": enriched_results}

# ================= HISTORY =================
@app.get("/query-history")
def history(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT nl_query, dsl, created_at FROM query_history WHERE user_id=%s ORDER BY created_at DESC", (current_user["user_id"],))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"history": rows}

# ================= DYNAMIC EXPLAIN RESULTS (UPDATED) =================
@app.post("/explain-results")
def explain_results(
    payload: ExplainRequest, 
    current_user: dict = Depends(get_current_user)
):
    # --- 1. DYNAMIC LOGIC GENERATOR ---
    insights = []

    # Analyze Valuation (PE)
    if payload.avg_pe < 15:
        val_insight = "📉 **Undervalued:** The average PE is low (<15), suggesting these stocks are in **value territory** and may be overlooked by the market."
    elif payload.avg_pe > 30:
        val_insight = "🚀 **High Growth:** The average PE is high (>30). Investors are paying a premium expecting **significant future growth**."
    else:
        val_insight = "⚖️ **Fair Value:** The average PE is moderate (15-30), aligning with historical market averages."
    insights.append(val_insight)

    # Analyze Income (Dividend)
    if payload.avg_dividend > 2.5:
        div_insight = "💰 **Income Generators:** With an average yield > 2.5%, this group is excellent for **dividend-focused portfolios**."
    elif payload.avg_dividend < 1.0:
        div_insight = "🌱 **Growth Focused:** Low dividend yields suggest these companies are **reinvesting profits** rather than paying them out."
    else:
        div_insight = "💵 **Balanced Income:** These stocks offer a modest mix of growth and steady income."
    insights.append(div_insight)

    # Analyze Sector Concentration
    if payload.sector_summary:
        # Find the sector with the highest count
        top_sector = max(payload.sector_summary, key=payload.sector_summary.get)
        count = payload.sector_summary[top_sector]
        sec_insight = f"🏭 **Sector Bet:** The results are heavily concentrated in **{top_sector}** ({count} stocks), which increases exposure to that specific industry's risks."
        insights.append(sec_insight)

    # --- 2. BUILD THE FINAL TEXT ---
    
    # Create bullet points
    bullet_points = "\n".join([f"- {i}" for i in insights])

    explanation = f"""
### 📊 AI Market Analysis

• **Overview:** Found stocks across **{len(payload.sector_summary)} sectors**.
• **Key Stats:** Avg PE: **{payload.avg_pe:.2f}** | Avg Yield: **{payload.avg_dividend:.2f}%**

📌 **Dynamic Interpretation:**
{bullet_points}

⚠️ *This insight is dynamically generated based on the screened metrics.*
"""

    return {"explanation": explanation}