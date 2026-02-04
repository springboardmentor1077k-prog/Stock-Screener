import sqlite3
import os
import sys

# Add parent directory to path to import tables
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tables.config import DB_PATH
from tables.alerts import get_schema as get_alerts_schema
from tables.alert_events import get_schema as get_events_schema

def init_alert_db():
    print(f"Initializing Alert System Database at: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create Alerts Table
        print("Creating 'alerts' table...")
        cursor.execute(get_alerts_schema())
        
        # Create Alert Events Table
        print("Creating 'alert_events' table...")
        cursor.execute(get_events_schema())
        
        conn.commit()
        print("Alert tables initialized successfully.")
        
    except Exception as e:
        print(f"Error initializing alert tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_alert_db()
