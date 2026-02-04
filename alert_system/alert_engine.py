import sqlite3
import pandas as pd
import os
import sys
import datetime

# Add parent directory to path to import tables
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tables.config import DB_PATH

class AlertEngine:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    # --- API: Create Alert ---
    def create_alert(self, user_id, portfolio_id, metric, operator, threshold):
        """
        Creates a new alert configuration.
        """
        sql = """
            INSERT INTO alerts (user_id, portfolio_id, metric, operator, threshold, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id, portfolio_id, metric, operator, threshold))
            conn.commit()
            alert_id = cursor.lastrowid
            print(f"Alert created successfully: ID {alert_id}")
            return alert_id
        except Exception as e:
            print(f"Error creating alert: {e}")
            return None
        finally:
            conn.close()

    # --- API: List User Alerts ---
    def list_user_alerts(self, user_id):
        """
        Fetches all alerts for a user.
        """
        sql = "SELECT * FROM alerts WHERE user_id = ?"
        conn = self._get_conn()
        try:
            df = pd.read_sql_query(sql, conn, params=(user_id,))
            return df.to_dict(orient='records')
        finally:
            conn.close()

    # --- API: Evaluate Alerts (Job) ---
    def evaluate_alerts(self):
        """
        Evaluates all active alerts using the defined pipeline.
        """
        print("Starting Alert Evaluation Pipeline...")
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            # 1. Alert Rule Selection (only is_active = true)
            active_alerts = pd.read_sql_query("SELECT * FROM alerts WHERE is_active = 1", conn)
            
            for _, alert in active_alerts.iterrows():
                alert_id = alert['id']
                portfolio_id = alert['portfolio_id']
                metric = alert['metric']
                operator = alert['operator']
                threshold = alert['threshold']
                
                print(f"Evaluating Alert ID {alert_id}: {metric} {operator} {threshold} for Portfolio {portfolio_id}")

                # 2. Scope Resolution: Fetch stock_ids from portfolio_holdings
                holdings_sql = "SELECT stock_id FROM portfolio_holdings WHERE portfolio_id = ?"
                holdings_df = pd.read_sql_query(holdings_sql, conn, params=(portfolio_id,))
                
                if holdings_df.empty:
                    print(f"  No holdings found for Portfolio {portfolio_id}. Skipping.")
                    continue
                
                stock_ids = holdings_df['stock_id'].tolist()
                placeholders = ','.join(['?'] * len(stock_ids))
                
                # 3. Metric Fetching
                # Note: Assuming 'metric' maps directly to column names in 'stocks' or 'analyst_ratings'
                # For this demo, we check 'stocks' table primarily, and 'analyst_ratings' for target_price/upside
                
                # Determine which table to query based on metric
                # Simple mapping logic
                if metric in ['price', 'pe_ratio', 'market_cap']:
                    table = 'stocks'
                    col = metric
                elif metric in ['target_price']:
                    table = 'analyst_ratings'
                    col = 'target_price'
                else:
                    # Fallback or error
                    print(f"  Unknown metric source for '{metric}'. Skipping.")
                    continue

                data_sql = f"SELECT symbol as stock_id, {col} as value FROM {table} WHERE symbol IN ({placeholders})"
                data_df = pd.read_sql_query(data_sql, conn, params=stock_ids)
                
                # 4. Condition Evaluation & 5. Trigger Decision Logic
                for _, row in data_df.iterrows():
                    stock_id = row['stock_id']
                    val = row['value']
                    
                    is_triggered = False
                    if operator == '>':
                        is_triggered = val > threshold
                    elif operator == '<':
                        is_triggered = val < threshold
                    elif operator == '=':
                        is_triggered = val == threshold
                    
                    if is_triggered:
                        # Check if already triggered (If condition is true AND no alert_event exists)
                        check_event_sql = "SELECT 1 FROM alert_events WHERE alert_id = ? AND stock_id = ?"
                        cursor.execute(check_event_sql, (alert_id, stock_id))
                        existing_event = cursor.fetchone()
                        
                        if not existing_event:
                            # 6. Event Recording
                            print(f"  [TRIGGERED] Stock: {stock_id}, Value: {val} (Threshold: {threshold})")
                            insert_sql = """
                                INSERT INTO alert_events (alert_id, stock_id, triggered_value)
                                VALUES (?, ?, ?)
                            """
                            cursor.execute(insert_sql, (alert_id, stock_id, val))
                            conn.commit() # Commit immediately for safety
                        else:
                            print(f"  [ALREADY TRIGGERED] Stock: {stock_id} (Event exists)")
                    else:
                        pass # Condition false -> do nothing

        except Exception as e:
            print(f"Error during evaluation: {e}")
        finally:
            conn.close()
            print("Alert Evaluation Pipeline Completed.")

if __name__ == "__main__":
    # Simple test if run directly
    engine = AlertEngine()
    print("Alert Engine Initialized.")
