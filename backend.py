from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

# -----------------------------
# Dummy user store
# -----------------------------
USERS = {
    "aishu@example.com": {
        "user_id": 1,
        "password": "1234"
    }
}

# token -> user_id mapping
TOKENS = {}

# -----------------------------
# Request models
# -----------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

# -----------------------------
# LOGIN API
# -----------------------------
@app.post("/login")
def login(data: LoginRequest):
    user = USERS.get(data.email)

    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # generate dummy token (no expiry)
    token = str(uuid.uuid4())

    TOKENS[token] = user["user_id"]

    return {
        "token": token
    }

# -----------------------------
# TOKEN VALIDATION
# -----------------------------
def validate_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token missing")

    token = authorization.replace("Bearer ", "")

    if token not in TOKENS:
        raise HTTPException(status_code=401, detail="Invalid token")

    return TOKENS[token]  # return user_id

# -----------------------------
# PROTECTED API
# -----------------------------
@app.get("/portfolio")
def get_portfolio(user_id: int = validate_token):
    # backend uses user_id from token
    return {
        "user_id": user_id,
        "portfolio": [
            {"stock": "AAPL", "quantity": 10},
            {"stock": "MSFT", "quantity": 5}
        ]
    }
