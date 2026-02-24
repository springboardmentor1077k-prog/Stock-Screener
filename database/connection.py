import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="stock_db",
        user="postgres",
        password="fatema00",
        cursor_factory=RealDictCursor
    )