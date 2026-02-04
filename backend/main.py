
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uuid

from parser import parse_query_to_dsl
from validator import validate_dsl
from screener import build_where_clause
from database import get_screening_data

# -------------------------
# APP INIT (THIS WAS MISSING / MOVED)
# -------------------------
app = FastAPI()

# -------------------------
# AUTH STORAGE (IN-MEMORY)
# -------------------------
users_db = {}
token_store = {}

# -------------------------
# REQUEST MODELS
# -------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ScreenRequest(BaseModel):
    query: str

# -------------------------
# ROUTES
# -------------------------
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
