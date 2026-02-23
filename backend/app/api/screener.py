from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal
from app.schemas.screener_schema import ScreenerRequest
from app.services.validator import validate_conditions
from app.services.compiler import compile_query
from app.core.security import get_current_user

router = APIRouter(prefix="/screener", tags=["Screener"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def run_screener(
    request: ScreenerRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        validate_conditions(request.conditions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    query, params = compile_query(request.conditions, request.logic)

    result = db.execute(text(query), params)
    rows = result.fetchall()

    return {"results": [dict(row._mapping) for row in rows]}