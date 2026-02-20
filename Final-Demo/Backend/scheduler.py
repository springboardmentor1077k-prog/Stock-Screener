from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
import yfinance as yf
from datetime import datetime
import logging

# CONFIG
DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG)

def check_alerts():
    """
    Checks all active alerts against current stock prices.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. Fetch all ACTIVE alerts
        cur.execute("""
            SELECT a.alert_id, a.user_id, s.ticker, a.metric, a.operator, a.threshold, s.stock_id
            FROM alerts a
            JOIN stocks s ON a.stock_id = s.stock_id
            WHERE a.status = 'active'
        """)
        active_alerts = cur.fetchall()

        if not active_alerts:
            return

        logger.info(f"🔍 Checking {len(active_alerts)} active alerts...")

        for alert in active_alerts:
            alert_id, user_id, ticker, metric, operator, threshold, stock_id = alert
            
            # 2. Fetch Current Price (Live)
            # Optimization: In a real app, you'd fetch all tickers at once to save API calls
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
                
                if not current_price:
                    continue

                # 3. Compare Logic
                is_triggered = False
                if operator == '>' and current_price > threshold:
                    is_triggered = True
                elif operator == '<' and current_price < threshold:
                    is_triggered = True
                elif operator == '>=' and current_price >= threshold:
                    is_triggered = True
                elif operator == '<=' and current_price <= threshold:
                    is_triggered = True

                # 4. If Triggered -> Save Event & Deactivate Alert (Optional)
                if is_triggered:
                    logger.info(f"🚨 ALERT TRIGGERED: {ticker} is {current_price} ({operator} {threshold})")
                    
                    # Insert into alert_events
                    cur.execute("""
                        INSERT INTO alert_events (user_id, alert_id, stock_id, triggered_value, triggered_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (user_id, alert_id, stock_id, current_price))
                    
                    # Optional: Mark alert as 'triggered' so it doesn't fire every 10 seconds
                    cur.execute("UPDATE alerts SET status = 'triggered' WHERE alert_id = %s", (alert_id,))
                    
                    conn.commit()

            except Exception as e:
                logger.error(f"Error checking {ticker}: {e}")

    except Exception as e:
        logger.error(f"Scheduler Error: {e}")
    finally:
        cur.close()
        conn.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run the check every 60 seconds (to avoid rate limits)
    scheduler.add_job(check_alerts, 'interval', seconds=60)
    scheduler.start()
    logger.info("🚀 Alert Scheduler Started!")