import sqlite3
import os
from utils.logging_config import logger

def get_db_path():
    # Use environment variable or default relative path
    default_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "analyst_demo", "stocks.db")
    return os.getenv("DB_PATH", default_path)

def get_db_connection():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        raise FileNotFoundError(f"Database not found at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise
