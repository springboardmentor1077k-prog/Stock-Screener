from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import logging

# We import settings from core (which we just created)
from app.core import settings

logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool: Optional[pool.SimpleConnectionPool] = None

def init_db_pool():
    """Initialize the database connection pool."""
    global _connection_pool
    
    if _connection_pool is None:
        try:
            db_uri = settings.DATABASE_URI
            _connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=db_uri
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

def close_db_pool():
    """Close all connections in the pool."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("Database connection pool closed")

@contextmanager
def get_db_connection():
    global _connection_pool
    if _connection_pool is None:
        init_db_pool()
    
    conn = _connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        _connection_pool.putconn(conn)

def execute_query(query: str, params: Optional[Tuple] = None) -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)

def fetch_one(query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            result = cur.fetchone()
            return dict(result) if result else None

def fetch_all(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            results = cur.fetchall()
            return [dict(row) for row in results] if results else []

def insert_returning(query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            result = cur.fetchone()
            return dict(result) if result else None

# --- DEPENDENCIES ---
def get_db():
    """Dependency for database connection."""
    with get_db_connection() as conn:
        yield conn
