from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database.connection import get_db_connection
import hashlib
import secrets
from datetime import datetime


router = APIRouter()


class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "stocksense_salt_2024"  # In production, use unique salt per user
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


@router.post("/register")
async def register_user(user: UserRegister):
    """Register a new user account."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if username exists
        cur.execute("SELECT id FROM users WHERE username = %s", (user.username,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email exists
        cur.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password and create user
        password_hash = hash_password(user.password)
        
        cur.execute("""
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (%s, %s, %s, %s)
            RETURNING id, username, email, full_name, created_at
        """, (user.username, user.email, password_hash, user.full_name))
        
        new_user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "message": "Registration successful",
            "user": {
                "id": new_user['id'],
                "username": new_user['username'],
                "email": new_user['email'],
                "full_name": new_user['full_name']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def login_user(credentials: UserLogin):
    """Authenticate user and return session token."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        password_hash = hash_password(credentials.password)
        
        cur.execute("""
            SELECT id, username, email, full_name, is_active
            FROM users 
            WHERE username = %s AND password_hash = %s
        """, (credentials.username, password_hash))
        
        user = cur.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not user['is_active']:
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        # Update last login
        cur.execute(
            "UPDATE users SET last_login = %s WHERE id = %s",
            (datetime.now(), user['id'])
        )
        conn.commit()
        
        # Generate simple session token
        session_token = secrets.token_hex(32)
        
        cur.close()
        conn.close()
        
        return {
            "message": "Login successful",
            "token": session_token,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "full_name": user['full_name']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{username}")
async def get_user_profile(username: str):
    """Get user profile information."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, username, email, full_name, created_at, last_login
            FROM users WHERE username = %s AND is_active = TRUE
        """, (username,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "full_name": user['full_name'],
            "member_since": user['created_at'].strftime("%B %Y") if user['created_at'] else None,
            "last_login": user['last_login'].strftime("%Y-%m-%d %H:%M") if user['last_login'] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
