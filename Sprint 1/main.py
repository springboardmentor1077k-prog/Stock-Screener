from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from llm_service import nl_to_dsl
from rule_compiler import compile_dsl_to_sql

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

# ================= HEALTH =================
@app.get("/health")
def health():
    try:
        conn = get_db()
        conn.close()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}

# ================= QUERY VALIDATION =================
def validate_query(query: str):
    q = query.lower()

    invalid_intents = [
        "predict", "forecast", "next quarter",
        "buy", "sell", "trade",
        "weather", "sports", "news",
        "write code", "generate", "hack"
    ]

    for word in invalid_intents:
        if word in q:
            return False, f"Unsupported query intent: '{word}'"

    valid_keywords = [
        "stock", "sector", "pe", "peg",
        "dividend", "ratio", "yield", "company"
    ]

    if not any(k in q for k in valid_keywords):
        return False, "Query does not look like a stock screening request"

    return True, ""

# ================= AUTH ===================
@app.post("/signup")
def signup(data: SignupRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE email=%s", (data.email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="User already exists")

    cur.execute(
        "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
        (data.email, hash_password(data.password))
    )

    conn.commit()
    cur.close()
    conn.close()
    return {"message": "User registered successfully"}

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT user_id, password_hash FROM users WHERE email=%s",
        (form.username,)
    )
    user = cur.fetchone()

    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": user["user_id"],
        "email": form.username
    })

    cur.close()
    conn.close()
    return {"access_token": token, "token_type": "bearer"}

# ================= FUNDAMENTALS DASHBOARD =================
@app.get("/stocks-with-fundamentals")
def stocks_with_fundamentals(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            s.stock_id,
            s.ticker,
            s.company_name,
            s.sector,
            f.pe_ratio,
            f.peg_ratio,
            f.dividend_yield,
            f.debt_to_equity
        FROM stocks s
        JOIN fundamentals f ON s.stock_id = f.stock_id
        ORDER BY s.company_name
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"data": rows}

# ================= NL QUERY =================
@app.post("/nl-query")
def process_query(
    payload: NLQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    is_valid, msg = validate_query(payload.query)
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    # NL → DSL
    dsl = nl_to_dsl(payload.query)

    # DSL → SQL WHERE
    where_clause = compile_dsl_to_sql(dsl)

    sql = f"""
        SELECT
            s.stock_id,
            s.ticker,
            s.company_name,
            s.sector,
            f.pe_ratio,
            f.peg_ratio,
            f.dividend_yield,
            f.debt_to_equity
        FROM stocks s
        JOIN fundamentals f ON s.stock_id = f.stock_id
        WHERE {where_clause}
        ORDER BY s.company_name
    """

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(sql)
    results = cur.fetchall()

    # Save history
    cur.execute("""
        INSERT INTO query_history (user_id, nl_query, dsl)
        VALUES (%s, %s, %s)
    """, (current_user["user_id"], payload.query, json.dumps(dsl)))

    conn.commit()
    cur.close()
    conn.close()

    return {
        "query": payload.query,
        "dsl": dsl,
        "results": results
    }

# ================= HISTORY =================
@app.get("/query-history")
def history(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT nl_query, dsl, created_at
        FROM query_history
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (current_user["user_id"],))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"history": rows}
@app.post("/explain-results")
def explain_results(data: dict, current_user: dict = Depends(get_current_user)):
    try:
        summary_prompt = f"""
        Explain the following stock screening result in simple terms for an investor.

        Sector distribution: {data.get("sector_summary")}
        Average PE: {data.get("avg_pe")}
        Average PEG: {data.get("avg_peg")}
        Dividend Yield: {data.get("avg_dividend")}
        """

        explanation = nl_to_dsl(summary_prompt, mode="explain")

        return {"explanation": explanation}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
class ExplainRequest(BaseModel):
    sector_summary: dict
    avg_pe: float
    avg_peg: float
    avg_dividend: float


@app.post("/explain-results")
def explain_results(
    payload: ExplainRequest,
    current_user: dict = Depends(get_current_user)
):
    explanation = f"""
### 📊 AI Insight Summary

• The screened stocks are primarily concentrated in **{', '.join(payload.sector_summary.keys())} sectors**.  
• The **average PE ratio is {payload.avg_pe:.2f}**, indicating overall valuation levels.  
• The **average PEG ratio is {payload.avg_peg:.2f}**, suggesting growth-adjusted pricing.  
• The **average dividend yield is {payload.avg_dividend:.2f}%**, reflecting income potential.

📌 **Interpretation**:
- Lower PE + PEG values generally indicate **undervalued growth stocks**.
- Higher dividend yield suggests **income-oriented investments**.
- Sector concentration helps identify **thematic investment opportunities**.

⚠️ *This insight is generated for educational purposes and should not be treated as financial advice.*
"""

    return {"explanation": explanation}
