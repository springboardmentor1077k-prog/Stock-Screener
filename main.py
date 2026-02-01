from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI()

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

fake_user = {
    "username": "admin",
    "password": "admin123"
}

class LoginRequest(BaseModel):
    username: str
    password: str

def create_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/login")
def login(data: LoginRequest):
    print("LOGIN RECEIVED:", data.username, data.password)
    if data.username != fake_user["username"] or data.password != fake_user["password"]:
        raise HTTPException(status_code=401, detail="Invalid login")
    return {"access_token": create_token(data.username)}

@app.get("/protected")
def protected(user: str = Depends(get_current_user)):
    return {"message": f"Welcome {user}, protected data!"}

@app.get("/")
def root():
    return {"message": "FastAPI is running"}




