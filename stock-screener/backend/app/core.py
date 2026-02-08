import logging
from typing import List, Union, Optional, Any, Dict, Generator
from datetime import datetime, timedelta
import bcrypt
from jose import jwt, JWTError
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# --- CONFIGURATION (from app/core/config.py) ---
class Settings(BaseSettings):
    PROJECT_NAME: str = "Stock Screener"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SUPER_SECRET_KEY_IN_PRODUCTION"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    DATABASE_URI: str = "postgresql://postgres:postgres@localhost:5432/stock_screener"
    DATABASE_PASSWORD: str = ""
    GEMINI_API_KEY: str = ""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "allow"

settings = Settings()

# --- LOGGING (from app/core/logging.py) ---
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

def get_logger(name: str):
    return logging.getLogger(name)

# --- SECURITY (from app/core/security.py) ---
def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            password=plain_password.encode("utf-8"),
            hashed_password=hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password=password.encode("utf-8"),
        salt=bcrypt.gensalt()
    ).decode("utf-8")