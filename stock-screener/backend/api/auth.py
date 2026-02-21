from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from backend.api.database import get_db
import hashlib
import secrets
import jwt
import os
import psycopg2
from psycopg2 import extras
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = "HS256"

def hash_password_safe(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return salt + ":" + password_hash

def verify_password_safe(password: str, stored_hash: str) -> bool:
    try:
        salt, password_hash = stored_hash.split(":", 1)
        test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return test_hash == password_hash
    except:
        return False

class Signup(BaseModel):
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

def create_access_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {"email": email, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("email")
        if email is None:
            return None
        return email
    except jwt.PyJWTError:
        return None

@router.post("/signup")
def signup(auth_data: Signup):
    db_connection = None
    db_cursor = None
    
    try:
        if len(auth_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        if len(auth_data.password) > 100:
            raise HTTPException(status_code=400, detail="Password is too long")
        
        db_connection = get_db()
        db_cursor = db_connection.cursor()
            
        db_cursor.execute("SELECT email FROM users WHERE email = %s", (auth_data.email,))
        if db_cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = hash_password_safe(auth_data.password)
        db_cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (auth_data.email.lower().strip(), hashed_password)
        )
        db_connection.commit()
        return {"status": "user created", "email": auth_data.email.lower().strip()}
        
    except HTTPException:
        if db_connection:
            db_connection.rollback()
        raise
    except Exception as e:
        if db_connection:
            db_connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if db_cursor:
            db_cursor.close()
        if db_connection:
            db_connection.close()

@router.post("/login")
def login(auth_data: Login):
    db_connection = None
    db_cursor = None
    
    try:
        db_connection = get_db()
        db_cursor = db_connection.cursor(cursor_factory=extras.RealDictCursor)
        
        db_cursor.execute("SELECT email, password_hash FROM users WHERE email = %s", (auth_data.email.lower().strip(),))
        user = db_cursor.fetchone()
        
        if not user or not verify_password_safe(auth_data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")        
        token = create_access_token(auth_data.email.lower().strip())
        return {"status": "login successful", "token": token, "email": user['email']}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if db_cursor:
            db_cursor.close()
        if db_connection:
            db_connection.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Authentication dependency that validates JWT token and returns user info.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = verify_token(credentials.credentials)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db_connection = None
    db_cursor = None
    
    try:
        db_connection = get_db()
        db_cursor = db_connection.cursor(cursor_factory=extras.RealDictCursor)
        
        db_cursor.execute("SELECT user_id, email FROM users WHERE email = %s", (email,))
        user_record = db_cursor.fetchone()
        
        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return {
            "user_id": user_record["user_id"],
            "email": user_record["email"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if db_cursor:
            db_cursor.close()
        if db_connection:
            db_connection.close()