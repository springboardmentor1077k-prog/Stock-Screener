from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/screener", tags=["Screener"])


@router.post("/run")
def run_screener(
    filters: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Example filters:
    {
      "pe_ratio": {"lt": 20},
      "market_cap": {"gt": 1000000000}
    }
    """

    query = "SELECT * FROM stocks s JOIN fundamentals f ON s.stock_id=f.stock_id WHERE 1=1"
    params = {}

    if "pe_ratio" in filters:
        query += " AND f.pe_ratio < :pe"
        params["pe"] = filters["pe_ratio"]["lt"]

    if "market_cap" in filters:
        query += " AND s.market_cap > :mc"
        params["mc"] = filters["market_cap"]["gt"]

    result = db.execute(text(query), params).fetchall()
    return result
