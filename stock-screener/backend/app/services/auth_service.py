
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserLogin
from app.core.security import verify_password, create_access_token

class AuthService:
    @staticmethod
    def signup(db: Session, user_in: UserCreate):
        user = UserRepository.get_user_by_email(db, user_in.email)
        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
        return UserRepository.create_user(db, user_in)

    @staticmethod
    def login(db: Session, user_in: UserLogin):
        user = UserRepository.get_user_by_email(db, user_in.email)
        if not user or not verify_password(user_in.password, user.hashed_password):
            return None
        return create_access_token(subject=user.email)
