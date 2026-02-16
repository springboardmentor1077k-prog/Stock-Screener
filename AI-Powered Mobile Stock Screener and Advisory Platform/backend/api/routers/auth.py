# Authentication API Router
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import timedelta
from ...models.schemas import UserCreate, UserLogin, Token
from ...auth.jwt_handler import authenticate_user, create_access_token, create_refresh_token, get_password_hash, verify_token
from ...database.connection import get_db
from ...models.database import User

auth_router = APIRouter()

@auth_router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    from ...core.utils import handle_database_error
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        hashed_password = get_password_hash(user.password)
        
        # Create new user
        db_user = User(
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create access and refresh tokens
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        handle_database_error(e)

@auth_router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.
    """
    from ...core.utils import handle_database_error
    
    try:
        user = authenticate_user(db, user_credentials.email, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        handle_database_error(e)

@auth_router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    from ...core.utils import handle_database_error
    
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        # Verify the refresh token
        token_data = verify_token(refresh_token, credentials_exception, "refresh")
        
        # Get user from database to ensure they still exist
        user = db.query(User).filter(User.email == token_data.email).first()
        if not user:
            raise credentials_exception
        
        # Create new access token
        access_token_expires = timedelta(minutes=30)
        new_access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user.email}
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        handle_database_error(e)