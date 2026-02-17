from fastapi import FastAPI, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, text
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import traceback
from llm_service import call_llm
import json


from config import DATABASE_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from dsl_compiler import compile_dsl

# =========================================================
# APP INIT
# =========================================================
app = FastAPI(title="AI Stock Screener Backend")

engine = create_engine(DATABASE_URL)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =========================================================
# FIELD MAPPING
# =========================================================
allowed_fields = {
    "pe_ratio": "f.pe_ratio",
    "revenue": "f.revenue",
    "sector": "c.sector"
}

# =========================================================
# 🔐 AUTH HELPERS
# =========================================================

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# =========================================================
# 🔐 REGISTER
# =========================================================
@app.post("/register")
def register(data: dict = Body(...)):
    try:
        hashed_password = hash_password(data["password"])

        sql = """
        INSERT INTO users (username, email, password_hash)
        VALUES (:username, :email, :password_hash)
        """

        with engine.connect() as conn:
            conn.execute(text(sql), {
                "username": data["username"],
                "email": data["email"],
                "password_hash": hashed_password
            })
            conn.commit()

        return {"message": "User registered successfully"}

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

# =========================================================
# 🔐 LOGIN
# =========================================================
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    sql = "SELECT user_id, password_hash FROM users WHERE username=:username"

    with engine.connect() as conn:
        user = conn.execute(text(sql), {
            "username": form_data.username
        }).fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(form_data.password, user[1]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user[0]})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# =========================================================
# 🔎 SCREEN (PROTECTED + LLM ENABLED)
# =========================================================
USE_REAL_LLM =False   # 🔥 Switch True to use Gemini

@app.get("/screen")
def screen(query: str, user_id: int = Depends(get_current_user)):

    try:
        print("\n🔹 SCREEN ENDPOINT CALLED")
        print("User:", user_id)
        print("Query:", query)

        # =================================================
        # 1️⃣ GET DSL FROM LLM OR MOCK
        # =================================================
        if USE_REAL_LLM:
            print("Using REAL Gemini LLM")

            llm_response = call_llm(query)
            print("Raw LLM Response:", llm_response)

            # 🔥 Clean possible markdown JSON
            cleaned = llm_response.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()

            dsl = json.loads(cleaned)

        else:
            print("Using MOCK DSL")

            dsl = {
                "logic": "AND",
                "conditions": [
                    {"field": "pe_ratio", "operator": "<", "value": 25},
                    {
                        "logic": "OR",
                        "conditions": [
                            {"field": "sector", "operator": "=", "value": "IT"},
                            {"field": "sector", "operator": "=", "value": "Energy"}
                        ]
                    }
                ]
            }

        print("Generated DSL:", dsl)
        # 2️⃣ Validate DSL
        if not dsl or "conditions" not in dsl:
            return {"error": "Invalid query format. Please enter a valid filter like: pe_ratio < 25"}

        # =================================================
        # 2️⃣ COMPILE DSL
        # =================================================
        sql_fragment, params = compile_dsl(dsl, allowed_fields)

        if not sql_fragment.strip():
            return {"error": "Invalid query format. Please refine your query."}
        # =================================================
        # 3️⃣ FINAL QUERY WITH ANALYST JOIN
        # =================================================
        sql = f"""
        SELECT DISTINCT 
               c.symbol,
               c.company_name,
               c.sector,
               f.pe_ratio,
               f.revenue,
               a.cost_price,
               a.target_price,
               ((a.target_price - a.cost_price) / a.cost_price) * 100 AS upside_percent
        FROM company_master c
        LEFT JOIN fundamental_data f
            ON c.company_id = f.company_id
        LEFT JOIN analyst_tactics a
            ON c.company_id = a.company_id
        WHERE {sql_fragment}
        ORDER BY upside_percent DESC NULLS LAST;
        """

        print("Generated SQL:", sql)
        print("Params:", params)

        # =================================================
        # 4️⃣ EXECUTE
        # =================================================
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()

        # =================================================
        # 5️⃣ RESPONSE
        # =================================================
        if not rows:
            return {
                "count": 0,
                "results": [],
                "message": "No matching stocks found"
            }

        results = []

        for r in rows:
            results.append({
                "symbol": r[0],
                "company_name": r[1],
                "sector": r[2],
                "pe_ratio": float(r[3]) if r[3] else None,
                "revenue": float(r[4]) if r[4] else None,
                "cost_price": float(r[5]) if r[5] else None,
                "target_price": float(r[6]) if r[6] else None,
                "upside_percent": float(r[7]) if r[7] else None
            })

        return {
            "count": len(results),
            "results": results
        }

    except Exception as e:
        print("\n🔥 FULL ERROR TRACE:")
        traceback.print_exc()
        return {"error": str(e)}

# =========================================================
# 🚨 CREATE ALERT (PROTECTED)
# =========================================================
# =========================================================
# 🚨 CREATE ALERT + AUTO EVALUATE (PROTECTED)
# =========================================================
@app.post("/alerts")
def create_alert(alert: dict = Body(...),
                 user_id: int = Depends(get_current_user)):

    try:
        with engine.connect() as conn:

            # 1️⃣ Insert alert
            insert_sql = """
            INSERT INTO alerts (portfolio_id, operation, metric, threshold, user_id)
            VALUES (:portfolio_id, :operation, :metric, :threshold, :user_id)
            RETURNING alert_id
            """

            alert["user_id"] = user_id

            result = conn.execute(text(insert_sql), alert)
            alert_id = result.fetchone()[0]

            # 2️⃣ Auto evaluate immediately
            if alert["metric"] == "upside_percent":

                eval_sql = f"""
                SELECT c.company_id,
                       c.symbol,
                       ((a.target_price - a.cost_price) / a.cost_price) * 100 AS upside
                FROM company_master c
                JOIN analyst_tactics a
                  ON c.company_id = a.company_id
                WHERE ((a.target_price - a.cost_price) / a.cost_price) * 100
                      {alert["operation"]} :threshold
                """

                stocks = conn.execute(
                    text(eval_sql),
                    {"threshold": alert["threshold"]}
                ).fetchall()

                for stock in stocks:

                    # 🚫 Prevent duplicate alert events
                    duplicate_check = conn.execute(text("""
                        SELECT 1 FROM alert_events
                        WHERE alert_id = :alert_id
                        AND stock_id = :stock_id
                    """), {
                        "alert_id": alert_id,
                        "stock_id": stock[0]
                    }).fetchone()

                    if not duplicate_check:
                        conn.execute(text("""
                            INSERT INTO alert_events
                            (alert_id, stock_id, triggered_value)
                            VALUES (:alert_id, :stock_id, :triggered_value)
                        """), {
                            "alert_id": alert_id,
                            "stock_id": stock[0],
                            "triggered_value": stock[2]
                        })

            conn.commit()

        return {"message": "Alert created and evaluated successfully"}

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

    
  # =========================================================
# 📢 GET ALERT EVENTS (PROTECTED)
# =========================================================
@app.get("/alert-events")
def get_alert_events(user_id: int = Depends(get_current_user)):

    try:
        sql = """
        SELECT e.event_id,
               c.symbol,
               c.company_name,
               a.metric,
               e.triggered_value,
               e.triggered_at
        FROM alert_events e
        JOIN alerts a ON e.alert_id = a.alert_id
        JOIN company_master c ON e.stock_id = c.company_id
        WHERE a.user_id = :user_id
        ORDER BY e.triggered_at DESC
        """

        with engine.connect() as conn:
            rows = conn.execute(text(sql), {"user_id": user_id}).fetchall()

        events = [
            {
                "event_id": r[0],
                "symbol": r[1],
                "company_name": r[2],
                "metric": r[3],
                "triggered_value (%)": float(r[4]),
                "triggered_at": r[5]
            }
            for r in rows
        ]

        return {"events": events}

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
