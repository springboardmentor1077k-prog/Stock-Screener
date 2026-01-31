
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def signup(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    return AuthService.signup(db, user_in)

@router.post("/login")
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    # Compatible with OAuth2PasswordRequestForm (username=email)
    user_in = UserLogin(email=form_data.username, password=form_data.password)
    token = AuthService.login(db, user_in)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return {"access_token": token, "token_type": "bearer"}
