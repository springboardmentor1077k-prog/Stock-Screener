"""
Alert Service Module - Database-wide alerts implementation.

This module implements alerts that monitor all stocks in the database:
1. Fetch active alerts
2. For each alert, evaluate all stocks in stocks_master
3. Record event when any stock meets the condition
"""

from db import get_db
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


class AlertService:
    """Service for managing and evaluating database-wide alerts."""
    
    # Supported metrics and their table mapping
    METRIC_MAPPING = {
        'pe_ratio': ('fundamentals', 'pe_ratio'),
        'peg_ratio': ('fundamentals', 'peg_ratio'),
        'debt': ('fundamentals', 'debt'),
        'free_cash_flow': ('fundamentals', 'free_cash_flow'),
        'revenue': ('quarterly_financials', 'revenue'),
        'ebitda': ('quarterly_financials', 'ebitda'),
        'net_profit': ('quarterly_financials', 'net_profit'),
        'current_market_price': ('analyst_targets', 'current_market_price'),
        'target_price_high': ('analyst_targets', 'target_price_high'),
        'target_price_low': ('analyst_targets', 'target_price_low'),
    }
    
    VALID_OPERATORS = ['<', '>', '<=', '>=', '=']

    def __init__(self):
        # Exposes evaluation diagnostics to API layer.
        self.last_eval_metrics = {
            "evaluated_alerts": 0,
            "triggered_alerts": 0,
            "already_triggered_recently": 0
        }
    
    def create_alert(
        self,
        user_id: int,
        portfolio_id: Optional[int],
        metric: str,
        operator: str,
        threshold: float
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new database-wide alert.
        
        Args:
            user_id: User ID creating the alert
            portfolio_id: Optional portfolio reference for backward compatibility
            metric: Metric to track (pe_ratio, price, etc.)
            operator: Comparison operator (<, >, <=, >=, =)
            threshold: Value to trigger alert
        
        Returns:
            Tuple of (success, message, alert_id)
        """
        # Validate inputs
        if metric not in self.METRIC_MAPPING:
            return False, f"Unsupported metric: {metric}", None
        
        if operator not in self.VALID_OPERATORS:
            return False, f"Invalid operator: {operator}", None
        
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            resolved_portfolio_id = portfolio_id
            if resolved_portfolio_id is None:
                cursor.execute(
                    """
                    SELECT id
                    FROM portfolios
                    WHERE user_id = %s
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (user_id,)
                )
                portfolio = cursor.fetchone()
                if not portfolio:
                    conn.close()
                    return False, "No portfolio found for user", None
                resolved_portfolio_id = portfolio["id"]
            
            # Keep portfolio_id for backward compatibility with existing schema/UI.
            cursor.execute("""
                INSERT INTO alerts 
                (user_id, portfolio_id, metric, operator, threshold, is_active, status)
                VALUES (%s, %s, %s, %s, %s, TRUE, 'active')
            """, (user_id, resolved_portfolio_id, metric, operator, threshold))
            
            alert_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return True, "Database-wide alert created", alert_id
        
        except Exception as e:
            return False, f"Error creating alert: {str(e)}", None
    
    def get_user_alerts(self, user_id: int) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Get all alerts for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Tuple of (success, message, alerts_list)
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            
            # Get alerts with event counts (no JOIN with stocks_master needed)
            cursor.execute("""
                SELECT 
                    a.id,
                    a.user_id,
                    a.portfolio_id,
                    a.metric,
                    a.operator,
                    a.threshold,
                    a.is_active,
                    a.status,
                    a.created_at,
                    (SELECT COUNT(*) FROM alert_events WHERE alert_id = a.id) as trigger_count,
                    (SELECT MAX(triggered_at) FROM alert_events WHERE alert_id = a.id) as last_triggered
                FROM alerts a
                WHERE a.user_id = %s
                ORDER BY a.created_at DESC
            """, (user_id,))
            
            alerts = cursor.fetchall()
            conn.close()
            
            return True, f"Found {len(alerts)} alerts", alerts
        
        except Exception as e:
            return False, f"Error fetching alerts: {str(e)}", []
    
    def delete_alert(self, alert_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete an alert (only if owned by user).
        
        Args:
            alert_id: Alert ID to delete
            user_id: User ID (for ownership verification)
        
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # First verify the alert belongs to this user
            cursor.execute(
                "SELECT id FROM alerts WHERE id = %s AND user_id = %s",
                (alert_id, user_id)
            )
            alert = cursor.fetchone()
            
            if not alert:
                conn.close()
                return False, "Alert not found or not authorized"
            
            # Delete related alert_events first (foreign key constraint)
            cursor.execute(
                "DELETE FROM alert_events WHERE alert_id = %s",
                (alert_id,)
            )
            
            # Now delete the alert itself
            cursor.execute(
                "DELETE FROM alerts WHERE id = %s AND user_id = %s",
                (alert_id, user_id)
            )
            
            conn.commit()
            conn.close()
            
            return True, "Alert deleted successfully"
        
        except Exception as e:
            return False, f"Error deleting alert: {str(e)}"
    
    def evaluate_alerts(self, user_id: Optional[int] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Evaluate all active alerts and record events.
        
        For database-wide alerts:
        1. Fetch active alerts
        2. For each alert, evaluate all stocks in stocks_master
        3. Evaluate condition for each stock
        4. Record event if any stock triggers the alert
        
        Args:
            user_id: Optional user_id to evaluate only their alerts
        
        Returns:
            Tuple of (success, message, triggered_alerts)
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            
            # Fetch active alerts
            if user_id:
                cursor.execute("""
                    SELECT 
                        a.id as alert_id,
                        a.metric,
                        a.operator,
                        a.threshold
                    FROM alerts a
                    WHERE a.is_active = TRUE AND a.user_id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT 
                        a.id as alert_id,
                        a.metric,
                        a.operator,
                        a.threshold
                    FROM alerts a
                    WHERE a.is_active = TRUE
                """)
            
            alerts = cursor.fetchall()
            triggered_alerts = []
            already_triggered_recently = 0
            
            # Evaluate against all stocks in the database
            cursor.execute("""
                SELECT id AS stock_id, symbol, company_name
                FROM stocks_master
            """)
            all_stocks = cursor.fetchall()
            
            # Evaluate each alert
            for alert in alerts:
                alert_id = alert['alert_id']
                metric = alert['metric']
                operator = alert['operator']
                threshold = alert['threshold']
                
                # Evaluate each stock in the database
                for stock in all_stocks:
                    stock_id = stock['stock_id']
                    symbol = stock['symbol']
                    company_name = stock['company_name']
                    
                    # Fetch current metric value
                    value = self._fetch_metric_value(cursor, stock_id, metric)
                    
                    if value is None:
                        continue  # Skip if metric not available
                    
                    # Evaluate condition
                    if self._evaluate_condition(value, operator, threshold):
                        # Ensure alert bucket exists for response aggregation.
                        if not any(t['alert_id'] == alert_id for t in triggered_alerts):
                            triggered_alerts.append({
                                'alert_id': alert_id,
                                'scope': 'database',
                                'metric': metric,
                                'operator': operator,
                                'threshold': threshold,
                                'triggered_stocks': []
                            })

                        # Check if already triggered recently (within 1 hour)
                        cursor.execute("""
                            SELECT id FROM alert_events
                            WHERE alert_id = %s 
                            AND stock_id = %s
                            AND triggered_at > %s
                            ORDER BY triggered_at DESC
                            LIMIT 1
                        """, (alert_id, stock_id, datetime.now() - timedelta(hours=1)))
                        
                        recent_event = cursor.fetchone()
                        
                        if not recent_event:
                            # Record new event
                            self._record_event(cursor, alert_id, stock_id, value)
                            event_status = "new_trigger"
                        else:
                            already_triggered_recently += 1

                            event_status = "already_triggered_recently"

                        # Always include matched stocks in response,
                        # even if event recording is throttled.
                        for ta in triggered_alerts:
                            if ta['alert_id'] == alert_id:
                                ta['triggered_stocks'].append({
                                    'symbol': symbol,
                                    'company_name': company_name,
                                    'triggered_value': float(value),
                                    'event_status': event_status
                                })
                                break
            
            conn.commit()
            conn.close()

            self.last_eval_metrics = {
                "evaluated_alerts": len(alerts),
                "triggered_alerts": len(triggered_alerts),
                "already_triggered_recently": already_triggered_recently
            }
            
            return True, f"Evaluated {len(alerts)} alerts, {len(triggered_alerts)} triggered", triggered_alerts
        
        except Exception as e:
            self.last_eval_metrics = {
                "evaluated_alerts": 0,
                "triggered_alerts": 0,
                "already_triggered_recently": 0
            }
            return False, f"Error evaluating alerts: {str(e)}", []
    
    def _fetch_metric_value(
        self,
        cursor,
        stock_id: int,
        metric: str
    ) -> Optional[float]:
        """
        Fetch current value of a metric for a stock.
        
        Args:
            cursor: Database cursor
            stock_id: Stock ID
            metric: Metric name
        
        Returns:
            Current metric value or None
        """
        if metric not in self.METRIC_MAPPING:
            return None
        
        table, column = self.METRIC_MAPPING[metric]
        
        try:
            # For quarterly financials, get most recent quarter
            if table == 'quarterly_financials':
                cursor.execute(f"""
                    SELECT {column}
                    FROM {table}
                    WHERE stock_id = %s
                    ORDER BY year DESC, quarter DESC
                    LIMIT 1
                """, (stock_id,))
            else:
                cursor.execute(f"""
                    SELECT {column}
                    FROM {table}
                    WHERE stock_id = %s
                    LIMIT 1
                """, (stock_id,))
            
            result = cursor.fetchone()
            return float(result[column]) if result and result[column] is not None else None
        
        except Exception:
            return None
    
    def _evaluate_condition(
        self,
        value: float,
        operator: str,
        threshold: float
    ) -> bool:
        """
        Evaluate if condition is met.
        
        Args:
            value: Current value
            operator: Comparison operator
            threshold: Threshold value
        
        Returns:
            True if condition met, False otherwise
        """
        if operator == '<':
            return value < threshold
        elif operator == '>':
            return value > threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '=':
            return abs(value - threshold) < 0.01  # Floating point comparison
        else:
            return False
    
    def _record_event(
        self,
        cursor,
        alert_id: int,
        stock_id: int,
        triggered_value: float
    ) -> None:
        """
        Record an alert trigger event.
        
        Args:
            cursor: Database cursor
            alert_id: Alert ID
            stock_id: Stock ID that triggered
            triggered_value: Value that triggered the alert
        """
        cursor.execute("""
            INSERT INTO alert_events 
            (alert_id, stock_id, triggered_value)
            VALUES (%s, %s, %s)
        """, (alert_id, stock_id, triggered_value))


# Singleton instance
alert_service = AlertService()
