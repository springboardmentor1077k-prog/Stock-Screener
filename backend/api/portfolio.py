from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.connection import get_db_connection
from typing import Optional, List

router = APIRouter()

class PortfolioHolding(BaseModel):
    portfolio_name: str = "Main Portfolio"
    symbol: str
    shares: int
    avg_buy_price: float

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = ""

@router.get("/profiles")
async def get_portfolio_profiles():
    """Get list of all portfolio profiles with summary stats."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                p.portfolio_name,
                COUNT(p.symbol) as holdings_count,
                COALESCE(SUM(p.shares * s.price), 0) as current_value,
                COALESCE(SUM(p.shares * p.avg_buy_price), 0) as invested_value,
                COALESCE(SUM((s.price - p.avg_buy_price) * p.shares), 0) as total_pl
            FROM portfolio p
            LEFT JOIN stocks s ON p.symbol = s.symbol
            GROUP BY p.portfolio_name
            ORDER BY current_value DESC
        """)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        profiles = []
        for r in results:
            invested = float(r['invested_value'] or 0)
            pl = float(r['total_pl'] or 0)
            pl_pct = (pl / invested * 100) if invested > 0 else 0
            profiles.append({
                "name": r['portfolio_name'],
                "holdings_count": r['holdings_count'],
                "current_value": round(float(r['current_value'] or 0), 2),
                "invested_value": round(invested, 2),
                "total_pl": round(pl, 2),
                "pl_percentage": round(pl_pct, 2)
            })
        
        return profiles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_portfolio_summary(portfolio_name: Optional[str] = None):
    """Get portfolio summary with current value and P/L. Optionally filter by portfolio name."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if portfolio_name:
            query = """
            SELECT 
                COALESCE(SUM(p.shares * s.price), 0) as current_value,
                COALESCE(SUM((s.price - p.avg_buy_price) * p.shares), 0) as total_pl,
                COALESCE(SUM(p.shares * p.avg_buy_price), 0) as invested_value
            FROM portfolio p
            LEFT JOIN stocks s ON p.symbol = s.symbol
            WHERE p.portfolio_name = %s
            """
            cur.execute(query, (portfolio_name,))
        else:
            query = """
            SELECT 
                COALESCE(SUM(p.shares * s.price), 0) as current_value,
                COALESCE(SUM((s.price - p.avg_buy_price) * p.shares), 0) as total_pl,
                COALESCE(SUM(p.shares * p.avg_buy_price), 0) as invested_value
            FROM portfolio p
            LEFT JOIN stocks s ON p.symbol = s.symbol
            """
            cur.execute(query)
        
        res = cur.fetchone()
        cur.close()
        conn.close()
        
        current = float(res['current_value'] or 0)
        invested = float(res['invested_value'] or 0)
        pl = float(res['total_pl'] or 0)
        pl_pct = (pl / invested * 100) if invested > 0 else 0
        
        return {
            "portfolio_name": portfolio_name or "All Portfolios",
            "current_value": round(current, 2),
            "invested_value": round(invested, 2),
            "total_pl": round(pl, 2),
            "pl_percentage": round(pl_pct, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/holdings")
async def get_holdings(portfolio_name: Optional[str] = None):
    """Get all portfolio holdings with current prices. Optionally filter by portfolio name."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        base_query = """
        SELECT 
            p.id,
            p.portfolio_name,
            p.symbol,
            s.company_name,
            s.sector,
            s.sub_sector,
            p.shares,
            p.avg_buy_price,
            s.price as current_price,
            (s.price - p.avg_buy_price) * p.shares as pl,
            CASE WHEN p.avg_buy_price > 0 
                 THEN ((s.price - p.avg_buy_price) / p.avg_buy_price * 100) 
                 ELSE 0 END as pl_pct,
            s.pe_ratio,
            s.peg_ratio,
            s.price_vs_target
        FROM portfolio p
        LEFT JOIN stocks s ON p.symbol = s.symbol
        """
        
        if portfolio_name:
            query = base_query + " WHERE p.portfolio_name = %s ORDER BY s.sector, p.symbol"
            cur.execute(query, (portfolio_name,))
        else:
            query = base_query + " ORDER BY p.portfolio_name, s.sector, p.symbol"
            cur.execute(query)
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{
            "id": r['id'],
            "portfolio_name": r['portfolio_name'], 
            "symbol": r['symbol'], 
            "company_name": r['company_name'], 
            "sector": r['sector'],
            "sub_sector": r['sub_sector'],
            "shares": r['shares'], 
            "avg_buy_price": float(r['avg_buy_price']),
            "current_price": float(r['current_price'] or 0),
            "pl": round(float(r['pl'] or 0), 2),
            "pl_pct": round(float(r['pl_pct'] or 0), 2),
            "pe_ratio": float(r['pe_ratio'] or 0),
            "peg_ratio": float(r['peg_ratio'] or 0) if r['peg_ratio'] else None,
            "price_vs_target": r['price_vs_target']
        } for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
async def add_holding(holding: PortfolioHolding):
    """Add a new holding to portfolio."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if holding already exists in same portfolio
        cur.execute("""
            SELECT id, shares, avg_buy_price FROM portfolio 
            WHERE portfolio_name = %s AND symbol = %s
        """, (holding.portfolio_name, holding.symbol))
        existing = cur.fetchone()
        
        if existing:
            # Update existing holding with weighted average price
            old_shares = existing['shares']
            old_price = float(existing['avg_buy_price'])
            new_total_shares = old_shares + holding.shares
            new_avg_price = ((old_shares * old_price) + (holding.shares * holding.avg_buy_price)) / new_total_shares
            
            cur.execute("""
                UPDATE portfolio SET shares = %s, avg_buy_price = %s WHERE id = %s
            """, (new_total_shares, new_avg_price, existing['id']))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return {
                "message": f"Updated existing position. Now holding {new_total_shares} shares at avg ${new_avg_price:.2f}",
                "id": existing['id'],
                "action": "updated"
            }
        else:
            cur.execute("""
                INSERT INTO portfolio (portfolio_name, symbol, shares, avg_buy_price)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (holding.portfolio_name, holding.symbol, holding.shares, holding.avg_buy_price))
            
            new_id = cur.fetchone()['id']
            conn.commit()
            cur.close()
            conn.close()
            
            return {"message": "Holding added successfully", "id": new_id, "action": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update/{holding_id}")
async def update_holding(holding_id: int, shares: int, avg_buy_price: float):
    """Update shares and average price for a holding."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE portfolio SET shares = %s, avg_buy_price = %s WHERE id = %s RETURNING id
        """, (shares, avg_buy_price, holding_id))
        
        updated = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if not updated:
            raise HTTPException(status_code=404, detail="Holding not found")
        
        return {"message": "Holding updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove/{holding_id}")
async def remove_holding(holding_id: int):
    """Remove a holding from portfolio."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM portfolio WHERE id = %s RETURNING id", (holding_id,))
        deleted = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Holding not found")
        
        return {"message": "Holding removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/profile/{portfolio_name}")
async def delete_portfolio(portfolio_name: str):
    """Delete an entire portfolio and all its holdings."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM portfolio WHERE portfolio_name = %s RETURNING id", (portfolio_name,))
        deleted_count = len(cur.fetchall())
        conn.commit()
        cur.close()
        conn.close()
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        return {"message": f"Portfolio '{portfolio_name}' deleted with {deleted_count} holdings"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))