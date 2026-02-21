from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt
import os
from backend.api.database import get_db

router = APIRouter(prefix="/stocks", tags=["Stocks"])
security = HTTPBearer()


def get_user(token=Depends(security)):
    try:
        return jwt.decode(
            token.credentials,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"]
        )["email"]
    except:
        raise HTTPException(401, "Invalid token")


@router.get("/")
def list_stocks(user=Depends(get_user)):
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    db_cursor.execute("""
        SELECT s.symbol, s.company_name, s.sector,
               f.pe_ratio, f.eps, f.roe
        FROM stocks s
        LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
        ORDER BY s.company_name
    """)
    rows = db_cursor.fetchall()
    db_cursor.close()
    db_connection.close()
    return [
        {"symbol": r[0], "company": r[1], "sector": r[2],
         "pe_ratio": r[3], "eps": r[4], "roe": r[5]}
        for r in rows
    ]


@router.get("/overview")
def market_overview(user=Depends(get_user)):
    """Return high-level market statistics for the Dashboard."""
    db_connection = get_db()
    db_cursor = db_connection.cursor()

    db_cursor.execute("SELECT COUNT(*) FROM stocks")
    total_stocks = db_cursor.fetchone()[0]

    db_cursor.execute("SELECT AVG(pe_ratio) FROM fundamentals WHERE pe_ratio > 0")
    avg_pe = db_cursor.fetchone()[0] or 0

    db_cursor.execute("SELECT AVG(market_cap) FROM fundamentals WHERE market_cap > 0")
    avg_mc = db_cursor.fetchone()[0] or 0

    db_cursor.execute("SELECT COUNT(DISTINCT sector) FROM stocks WHERE sector IS NOT NULL AND sector != ''")
    active_sectors = db_cursor.fetchone()[0]

    db_cursor.close()
    db_connection.close()
    return {
        "total_stocks": total_stocks,
        "avg_pe_ratio": round(float(avg_pe), 2),
        "avg_market_cap": float(avg_mc),
        "active_sectors": active_sectors,
    }


@router.get("/top")
def top_companies(user=Depends(get_user), limit: int = 10):
    """Return top companies ranked by market cap."""
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    db_cursor.execute("""
        SELECT s.stock_id, s.symbol, s.company_name, s.sector, s.industry,
               f.market_cap, f.pe_ratio, f.dividend_yield, f.eps
        FROM stocks s
        LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
        WHERE f.market_cap IS NOT NULL AND f.market_cap > 0
        ORDER BY f.market_cap DESC
        LIMIT %s
    """, (limit,))
    rows = db_cursor.fetchall()
    db_cursor.close()
    db_connection.close()
    return [
        {
            "id": r[0], "symbol": r[1], "Company": r[2],
            "sector": r[3], "industry": r[4],
            "Market Cap": r[5], "PE Ratio": r[6],
            "div_yield": r[7], "EPS": r[8],
        }
        for r in rows
    ]
