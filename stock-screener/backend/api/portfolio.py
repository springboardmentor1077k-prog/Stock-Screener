from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from backend.api.auth import get_current_user
from backend.api.database import get_db
import psycopg2
from psycopg2 import extras
from datetime import datetime

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# ── Pydantic Models ───────────────────────────────────────────────────────────

class PortfolioCreate(BaseModel):
    name: str
    person_name: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_db_cursor(db_connection):
    return db_connection.cursor(cursor_factory=extras.RealDictCursor)

def verify_portfolio_ownership(db_cursor, portfolio_id: int, user_id: int):
    """Raise 404 if portfolio does not belong to user."""
    db_cursor.execute(
        "SELECT portfolio_id FROM portfolio WHERE portfolio_id=%s AND user_id=%s",
        (portfolio_id, user_id),
    )
    if not db_cursor.fetchone():
        raise HTTPException(status_code=404, detail="Portfolio not found")

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/summary")
async def get_portfolio_summary(current_user: dict = Depends(get_current_user)):
    """Summary metrics for the current user's portfolios."""
    db_connection = get_db()
    db_cursor = get_db_cursor(db_connection)
    try:
        db_cursor.execute("""
            SELECT
                COUNT(DISTINCT p.portfolio_id)                                    AS total_portfolios,
                COUNT(ph.holding_id)                                              AS total_holdings,
                COALESCE(SUM(ph.quantity * ph.avg_price), 0)                     AS total_invested,
                COALESCE(SUM(ph.quantity * f.current_price), 0)                  AS current_value,
                COALESCE(SUM(ph.quantity * f.current_price)
                        - SUM(ph.quantity * ph.avg_price), 0)                    AS total_gain_loss
            FROM portfolio p
            LEFT JOIN portfolio_holdings ph ON p.portfolio_id = ph.portfolio_id
            LEFT JOIN fundamentals      f  ON ph.stock_id     = f.stock_id
            WHERE p.user_id = %s
        """, (current_user["user_id"],))
        summary = db_cursor.fetchone()
        if summary["total_invested"] and summary["total_invested"] > 0:
            summary["gain_loss_percent"] = (
                summary["total_gain_loss"] / summary["total_invested"] * 100
            )
        else:
            summary["gain_loss_percent"] = 0
        return summary
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db_cursor.close(); db_connection.close()


@router.get("/")
async def get_user_portfolios(current_user: dict = Depends(get_current_user)):
    """List all portfolios (with screener-stock count) for the current user."""
    db_connection = get_db()
    db_cursor = get_db_cursor(db_connection)
    try:
        db_cursor.execute("""
            SELECT
                p.portfolio_id,
                p.user_id,
                p.name,
                p.person_name,
                p.created_at,
                COUNT(DISTINCT ph.holding_id)   AS total_holdings,
                COALESCE(SUM(ph.quantity * ph.avg_price), 0) AS total_value
            FROM portfolio p
            LEFT JOIN portfolio_holdings ph ON p.portfolio_id = ph.portfolio_id
            WHERE p.user_id = %s
            GROUP BY p.portfolio_id, p.user_id, p.name, p.person_name, p.created_at
            ORDER BY p.created_at DESC
        """, (current_user["user_id"],))
        return db_cursor.fetchall()
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db_cursor.close(); db_connection.close()


@router.post("/")
async def create_portfolio(
    portfolio_request: PortfolioCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new portfolio (optionally with a person name)."""
    if not portfolio_request.name.strip():
        raise HTTPException(status_code=400, detail="Portfolio name cannot be empty")
    db_connection = get_db()
    db_cursor = get_db_cursor(db_connection)
    try:
        db_cursor.execute("""
            INSERT INTO portfolio (user_id, name, person_name)
            VALUES (%s, %s, %s)
            RETURNING portfolio_id
        """, (current_user["user_id"], portfolio_request.name.strip(), portfolio_request.person_name))
        row = db_cursor.fetchone()
        db_connection.commit()
        return {"portfolio_id": row["portfolio_id"], "message": "Portfolio created successfully"}
    except psycopg2.IntegrityError:
        db_connection.rollback()
        raise HTTPException(status_code=400, detail="Portfolio name already exists for this user")
    except psycopg2.Error as e:
        db_connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db_cursor.close(); db_connection.close()


@router.get("/{portfolio_id}/holdings")
async def get_portfolio_holdings(
    portfolio_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Return all holdings for a specific portfolio."""
    db_connection = get_db()
    db_cursor = get_db_cursor(db_connection)
    try:
        verify_portfolio_ownership(db_cursor, portfolio_id, current_user["user_id"])
        db_cursor.execute("""
            SELECT
                ph.holding_id,
                ph.portfolio_id,
                ph.stock_id,
                s.symbol,
                s.company_name,
                ph.quantity,
                ph.avg_price,
                f.current_price,
                ph.quantity * ph.avg_price AS total_value,
                CASE WHEN f.current_price IS NOT NULL
                     THEN (f.current_price - ph.avg_price) * ph.quantity END         AS gain_loss,
                CASE WHEN f.current_price IS NOT NULL AND ph.avg_price > 0
                     THEN ((f.current_price - ph.avg_price) / ph.avg_price) * 100 END AS gain_loss_percent,
                ph.created_at,
                ph.updated_at
            FROM portfolio_holdings ph
            JOIN stocks      s  ON ph.stock_id = s.stock_id
            LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
            WHERE ph.portfolio_id = %s
            ORDER BY s.symbol
        """, (portfolio_id,))
        return db_cursor.fetchall()
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db_cursor.close(); db_connection.close()


@router.post("/{portfolio_id}/holdings")
async def add_holding(
    portfolio_id: int,
    holding_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Add / update a holding in a portfolio."""
    db_connection = get_db()
    db_cursor = get_db_cursor(db_connection)
    try:
        verify_portfolio_ownership(db_cursor, portfolio_id, current_user["user_id"])
        db_cursor.execute("""
            INSERT INTO portfolio_holdings (portfolio_id, stock_id, quantity, avg_price)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (portfolio_id, stock_id) DO UPDATE SET
                quantity  = portfolio_holdings.quantity + EXCLUDED.quantity,
                avg_price = ((portfolio_holdings.quantity * portfolio_holdings.avg_price)
                            + (EXCLUDED.quantity * EXCLUDED.avg_price))
                            / (portfolio_holdings.quantity + EXCLUDED.quantity)
            RETURNING holding_id
        """, (portfolio_id, holding_data["stock_id"], holding_data["quantity"], holding_data["avg_price"]))
        row = db_cursor.fetchone()
        db_connection.commit()
        return {"holding_id": row["holding_id"], "message": "Holding added successfully"}
    except psycopg2.Error as e:
        db_connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db_cursor.close(); db_connection.close()




@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    current_user: dict = Depends(get_current_user),
):
    db_connection = get_db()
    db_cursor = get_db_cursor(db_connection)
    try:
        verify_portfolio_ownership(db_cursor, portfolio_id, current_user["user_id"])
        db_cursor.execute("DELETE FROM portfolio WHERE portfolio_id=%s", (portfolio_id,))
        db_connection.commit()
        return {"message": "Portfolio deleted successfully"}
    except psycopg2.Error as e:
        db_connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db_cursor.close(); db_connection.close()


@router.delete("/{portfolio_id}/holdings/{holding_id}")
async def delete_holding(
    portfolio_id: int,
    holding_id: int,
    current_user: dict = Depends(get_current_user),
):
    db_connection = get_db()
    db_cursor = get_db_cursor(db_connection)
    try:
        db_cursor.execute("""
            SELECT ph.holding_id FROM portfolio_holdings ph
            JOIN portfolio p ON ph.portfolio_id = p.portfolio_id
            WHERE ph.holding_id=%s AND ph.portfolio_id=%s AND p.user_id=%s
        """, (holding_id, portfolio_id, current_user["user_id"]))
        if not db_cursor.fetchone():
            raise HTTPException(status_code=404, detail="Holding not found")
        db_cursor.execute("DELETE FROM portfolio_holdings WHERE holding_id=%s", (holding_id,))
        db_connection.commit()
        return {"message": "Holding deleted successfully"}
    except psycopg2.Error as e:
        db_connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db_cursor.close(); db_connection.close()