from fastapi import APIRouter, HTTPException, Query
from database.connection import get_db_connection
from typing import Optional
import traceback

router = APIRouter()

# Full field list for IT stock data
STOCK_FIELDS = """symbol, company_name, sector, sub_sector, price, change_pct, pe_ratio, 
                   market_cap, promoter_holding, has_buyback, revenue_growth,
                   q1_earnings, q2_earnings, q3_earnings, q4_earnings,
                   eps, dividend_yield, debt_to_equity, roe, exchange,
                   peg_ratio, earnings_growth_rate, free_cash_flow, total_debt, debt_to_fcf,
                   analyst_price_low, analyst_price_high, analyst_price_avg, price_vs_target,
                   revenue_growth_yoy, ebitda, ebitda_growth_yoy,
                   estimated_eps, historical_beat_rate, likely_to_beat,
                   next_earnings_date, earnings_within_30_days"""

@router.get("/")
async def get_all_stocks(
    sector: Optional[str] = None,
    sub_sector: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """Get all stocks with optional sector/sub-sector filter."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if sub_sector:
            cur.execute(f"""
                SELECT {STOCK_FIELDS}
                FROM stocks WHERE sub_sector = %s ORDER BY market_cap DESC LIMIT %s
            """, (sub_sector, limit))
        elif sector:
            cur.execute(f"""
                SELECT {STOCK_FIELDS}
                FROM stocks WHERE sector = %s ORDER BY market_cap DESC LIMIT %s
            """, (sector, limit))
        else:
            cur.execute(f"""
                SELECT {STOCK_FIELDS}
                FROM stocks ORDER BY market_cap DESC LIMIT %s
            """, (limit,))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return [dict(r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sectors")
async def get_sectors():
    """Get list of all sectors."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT sector FROM stocks ORDER BY sector")
        results = cur.fetchall()
        cur.close()
        conn.close()
        return [r['sector'] for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sub-sectors")
async def get_sub_sectors():
    """Get list of all IT sub-sectors."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT sub_sector FROM stocks WHERE sub_sector IS NOT NULL ORDER BY sub_sector")
        results = cur.fetchall()
        cur.close()
        conn.close()
        return [r['sub_sector'] for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_stocks(query: str):
    """Search stocks using natural language or direct filters."""
    try:
        # Try AI-powered search first
        from backend.logic.engine import run_screener
        result = run_screener(query)
        return result
    except Exception as e:
        # Fallback to simple text search
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            search_term = f"%{query}%"
            cur.execute(f"""
                SELECT {STOCK_FIELDS}
                FROM stocks 
                WHERE symbol ILIKE %s OR company_name ILIKE %s OR sector ILIKE %s OR sub_sector ILIKE %s
                ORDER BY market_cap DESC LIMIT 100
            """, (search_term, search_term, search_term, search_term))
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as inner_e:
            raise HTTPException(status_code=500, detail=f"Search failed: {str(inner_e)}")

@router.get("/{symbol}")
async def get_stock_detail(symbol: str):
    """Get detailed info for a specific stock."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT {STOCK_FIELDS}
            FROM stocks WHERE symbol = %s
        """, (symbol.upper(),))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        return dict(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))