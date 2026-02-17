from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from config import DATABASE_URL, SECRET_KEY, ALGORITHM

# ----------------------------
# DB
# ----------------------------
engine = create_engine(DATABASE_URL)

# ----------------------------
# Password Hashing
# ----------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----------------------------
# OAuth2
# ----------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# =====================================================
# 🔐 HASH PASSWORD
# =====================================================
def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# =====================================================
# 📝 REGISTER USER
# =====================================================
def register_user(username: str, email: str, password: str):

    hashed = hash_password(password)

    sql = """
    INSERT INTO users (username, email, password_hash)
    VALUES (:username, :email, :password_hash)
    """

    with engine.connect() as conn:
        conn.execute(text(sql), {
            "username": username,
            "email": email,
            "password_hash": hashed
        })
        conn.commit()


# =====================================================
# 🔑 AUTHENTICATE USER
# =====================================================
def authenticate_user(username: str, password: str):

    sql = """
    SELECT user_id, password_hash
    FROM users
    WHERE username = :username
    """

    with engine.connect() as conn:
        user = conn.execute(text(sql), {
            "username": username
        }).fetchone()

    if not user:
        return None

    user_id = user[0]
    hashed_password = user[1]

    if not verify_password(password, hashed_password):
        return None

    return user_id


# =====================================================
# 🎫 CREATE TOKEN
# =====================================================
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


# =====================================================
# 🔐 VERIFY TOKEN
# =====================================================
def get_current_user(token: str = Depends(oauth2_scheme)):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user_id

    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
