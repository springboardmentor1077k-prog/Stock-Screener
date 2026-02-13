from typing import List, Dict, Any
import hashlib
from utils.database import get_db_connection
from utils.logging_config import logger
from utils.exceptions import SystemException, ValidationException, DatabaseException, ServiceException
from utils.retries import db_retry

class AlertsService:
    @db_retry
    def get_alerts(self, portfolio_id: int = 1) -> List[Dict[str, Any]]:
        try:
            conn = get_db_connection()
            rows = conn.execute("SELECT * FROM alerts WHERE portfolio_id = ?", (portfolio_id,)).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Alerts fetch failure: {e}", exc_info=True)
            raise DatabaseException(f"Failed to fetch alerts: {str(e)}")

    @db_retry
    def create_alert(self, symbol: str, condition: str, value: float, user_id: int = 1, portfolio_id: int = 1) -> Dict[str, Any]:
        operator = ">" if "Above" in condition else "<"
        metric = f"{symbol} price"
        
        try:
            conn = get_db_connection()
            
            # Case 1: Duplicate alert protection
            # Check if an identical active alert already exists
            existing = conn.execute(
                "SELECT id FROM alerts WHERE portfolio_id = ? AND metric = ? AND operator = ? AND threshold = ? AND is_active = 1",
                (portfolio_id, metric, operator, value)
            ).fetchone()
            
            if existing:
                conn.close()
                logger.info(f"Duplicate alert attempt for {metric} {operator} {value}")
                raise ValidationException("Alert already exists.")

            conn.execute(
                "INSERT INTO alerts (user_id, portfolio_id, metric, operator, threshold, is_active) VALUES (?, ?, ?, ?, ?, 1)",
                (user_id, portfolio_id, metric, operator, value)
            )
            conn.commit()
            conn.close()
            return {"status": "success", "message": "Alert created"}
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Alert creation failure: {e}", exc_info=True)
            raise DatabaseException(f"Failed to create alert: {str(e)}")

    @db_retry
    def check_alerts(self, portfolio_id: int = 1) -> Dict[str, Any]:
        # This would normally call the AlertEngine
        # For brevity in this migration, we'll simulate the logic or try to import it
        try:
            # Reusing existing AlertEngine logic if possible
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "alert_system"))
            from alert_engine import AlertEngine
            
            from utils.database import get_db_path
            db_path = get_db_path()
            
            conn = get_db_connection()
            before_total = conn.execute("SELECT COUNT(*) FROM alert_events").fetchone()[0]
            
            engine = AlertEngine(db_path=db_path)
            engine.evaluate_alerts()
            
            after_total = conn.execute("SELECT COUNT(*) FROM alert_events").fetchone()[0]
            delta = after_total - before_total
            
            events_sql = """
            SELECT e.id, e.alert_id, e.stock_id, e.triggered_value, e.triggered_at
            FROM alert_events e
            JOIN alerts a ON a.id = e.alert_id
            WHERE a.portfolio_id = ?
            ORDER BY e.triggered_at DESC
            LIMIT 50
            """
            rows = conn.execute(events_sql, (portfolio_id,)).fetchall()
            conn.close()
            
            return {
                "status": "success",
                "message": "No new alerts fired" if delta == 0 else f"{delta} alert(s) fired",
                "metrics": {
                    "total_events": after_total,
                    "new_events": delta
                },
                "data": [dict(r) for r in rows]
            }
        except Exception as e:
            logger.error(f"Alert check failure: {e}", exc_info=True)
            raise ServiceException(f"Alert engine check failed: {str(e)}")

alerts_service = AlertsService()
