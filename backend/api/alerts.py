from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.connection import get_db_connection
from typing import Optional

router = APIRouter()

class AlertCreate(BaseModel):
    symbol: str
    metric: str  # 'price', 'pe_ratio', 'promoter_holding'
    condition: str  # '<', '>', '<=', '>=', '=='
    threshold: float

@router.get("/")
async def get_alerts():
    """Get all active alerts with current values."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
        SELECT 
            a.id, a.symbol, s.company_name, a.metric, a.condition, 
            a.threshold, a.status, a.triggered_count,
            CASE a.metric 
                WHEN 'price' THEN s.price
                WHEN 'pe_ratio' THEN s.pe_ratio
                WHEN 'promoter_holding' THEN s.promoter_holding
                ELSE NULL 
            END as current_value
        FROM alerts a
        LEFT JOIN stocks s ON a.symbol = s.symbol
        ORDER BY a.status DESC, a.id DESC
        """
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{"id": r['id'], "symbol": r['symbol'], "company_name": r['company_name'],
                 "metric": r['metric'], "condition": r['condition'],
                 "threshold": float(r['threshold']), "status": r['status'],
                 "triggered_count": r['triggered_count'],
                 "current_value": float(r['current_value']) if r['current_value'] else None} for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_alert(alert: AlertCreate):
    """Create a new price/metric alert."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verify stock exists
        cur.execute("SELECT symbol FROM stocks WHERE symbol = %s", (alert.symbol,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Stock {alert.symbol} not found")
        
        cur.execute("""
            INSERT INTO alerts (symbol, metric, condition, threshold)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (alert.symbol, alert.metric, alert.condition, alert.threshold))
        
        new_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        
        return {"message": "Alert created successfully", "id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{alert_id}")
async def delete_alert(alert_id: int):
    """Delete an alert."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM alerts WHERE id = %s RETURNING id", (alert_id,))
        deleted = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check")
async def check_triggered_alerts():
    """Check which alerts have been triggered."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all active alerts and check conditions
        query = """
        SELECT 
            a.id, a.symbol, s.company_name, a.metric, a.condition, a.threshold,
            CASE a.metric 
                WHEN 'price' THEN s.price
                WHEN 'pe_ratio' THEN s.pe_ratio
                WHEN 'promoter_holding' THEN s.promoter_holding
                ELSE NULL 
            END as current_value
        FROM alerts a
        JOIN stocks s ON a.symbol = s.symbol
        WHERE a.status = 'Active'
        """
        cur.execute(query)
        alerts = cur.fetchall()
        
        triggered = []
        for alert in alerts:
            cv = float(alert['current_value']) if alert['current_value'] else 0
            th = float(alert['threshold'])
            cond = alert['condition']
            
            is_triggered = False
            if cond == '>' and cv > th: is_triggered = True
            elif cond == '<' and cv < th: is_triggered = True
            elif cond == '>=' and cv >= th: is_triggered = True
            elif cond == '<=' and cv <= th: is_triggered = True
            elif cond == '==' and cv == th: is_triggered = True
            
            if is_triggered:
                triggered.append({
                    "id": alert['id'], "symbol": alert['symbol'],
                    "company_name": alert['company_name'], "metric": alert['metric'],
                    "condition": alert['condition'], "threshold": th, "current_value": cv
                })
                # Update triggered count
                cur.execute("UPDATE alerts SET triggered_count = triggered_count + 1 WHERE id = %s", (alert['id'],))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"triggered_count": len(triggered), "alerts": triggered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))