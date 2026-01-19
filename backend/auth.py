from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from backend.database import get_db
from backend.security import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["Auth"])

class Signup(BaseModel):
    email: EmailStr
    password: str

class Login(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
def signup(data: Signup):
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT user_id FROM users WHERE email=%s", (data.email,))
    if cur.fetchone():
        raise HTTPException(400, "User already exists")

    cur.execute(
        "INSERT INTO users (email, password_hash) VALUES (%s,%s)",
        (data.email, hash_password(data.password))
    )
    db.commit()
    cur.close()
    db.close()
    return {"message": "User created"}

@router.post("/login")
def login(data: Login):
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT user_id, password_hash FROM users WHERE email=%s",
        (data.email,)
    )
    user = cur.fetchone()

    if not user or not verify_password(data.password, user[1]):
        raise HTTPException(401, "Invalid credentials")

    return {"access_token": create_token(user[0])}
