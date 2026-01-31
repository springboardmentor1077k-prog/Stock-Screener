from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import psycopg2

# ---------------- CONFIG ----------------
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

# ---------------------------------------
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ---------------- DB --------------------
def get_db():
    return psycopg2.connect(**DATABASE_CONFIG)

# ---------------- UTILS -----------------
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------- SIGNUP ----------------
@app.post("/signup")
def signup(email: str, password: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(password)
    cur.execute(
        "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
        (email, hashed)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "User registered successfully"}

# ---------------- LOGIN -----------------
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT password_hash FROM users WHERE email=%s",
        (form_data.username,)
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row or not verify_password(form_data.password, row[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}

# ------------- PROTECTED ----------------
@app.get("/protected")
def protected(user: str = Depends(get_current_user)):
    return {"message": f"Hello {user}, this is protected data"}

# ---------- STOCK + FUNDAMENTALS (PROTECTED) ----------
@app.get("/stocks-with-fundamentals")
def get_stocks_with_fundamentals(user: str = Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            s.stock_id,
            s.company_name,
            s.sector,
            f.pe_ratio,
            f.peg_ratio
        FROM stocks s
        LEFT JOIN fundamentals f
        ON s.stock_id = f.stock_id
        ORDER BY s.company_name
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {
        "user": user,
        "data": [
            {
                "stock_id": r[0],
                "company_name": r[1],
                "sector": r[2],
                "pe_ratio": r[3],
                "peg_ratio": r[4],
            }
            for r in rows
        ]
    }
