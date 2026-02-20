import psycopg2

DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

def get_db():
    return psycopg2.connect(**DATABASE_CONFIG)
def get_connection():
    return psycopg2.connect(**DATABASE_CONFIG)