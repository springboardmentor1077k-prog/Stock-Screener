from alert_engine import AlertEngine
import pandas as pd

def run_demo():
    engine = AlertEngine()
    
    print("=== 1. Create Alerts ===")
    # Alert 1: PE Ratio < 15 for Portfolio 1 (User 101)
    # Portfolio 1 has AAPL, MSFT. Let's assume AAPL PE is around 30, MSFT 35. 
    # Wait, the mock data for stocks might be random or specific. 
    # Let's create an alert that SHOULD trigger.
    # Let's look at portfolio holdings for Portfolio 1: AAPL, MSFT.
    
    # Let's create an alert: Price > 100 for Portfolio 1
    alert1_id = engine.create_alert(
        user_id=101,
        portfolio_id=1,
        metric='price',
        operator='>',
        threshold=100.0
    )
    
    # Alert 2: Target Price > 200 for Portfolio 2 (User 101)
    # Portfolio 2 has NVDA, TSLA.
    alert2_id = engine.create_alert(
        user_id=101,
        portfolio_id=2,
        metric='target_price',
        operator='>',
        threshold=200.0
    )

    print("\n=== 2. List Alerts ===")
    alerts = engine.list_user_alerts(user_id=101)
    print(pd.DataFrame(alerts).to_markdown(index=False))

    print("\n=== 3. Run Evaluation Pipeline (Run 1) ===")
    engine.evaluate_alerts()

    print("\n=== 4. Check Alert Events ===")
    # Helper to view events
    import sqlite3
    conn = sqlite3.connect(engine.db_path)
    events_df = pd.read_sql_query("SELECT * FROM alert_events", conn)
    print(events_df.to_markdown(index=False))
    conn.close()

    print("\n=== 5. Run Evaluation Pipeline (Run 2 - Should not re-trigger) ===")
    engine.evaluate_alerts()

if __name__ == "__main__":
    run_demo()
