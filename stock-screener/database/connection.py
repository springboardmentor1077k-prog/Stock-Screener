import psycopg2
from psycopg2 import extras
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    """Get PostgreSQL database connection with support for DATABASE_URI for ingestion."""
    try:
        db_uri = os.getenv("DATABASE_URI")
        if db_uri:
            connection = psycopg2.connect(db_uri, connect_timeout=10)
        else:
            connection = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", 5432)),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                connect_timeout=10
            )
        connection.autocommit = False
        return connection
            
    except psycopg2.Error as e:
        error_msg = f"Database connection error: {e}"
        if hasattr(e, 'pgcode'):
            if e.pgcode == '28P01':
                error_msg = "Database authentication failed - check username/password"
            elif e.pgcode == '08001':
                error_msg = "Cannot connect to PostgreSQL server - check if it is running"
            elif e.pgcode == '3D000':
                error_msg = f"Database '{os.getenv('DB_NAME')}' does not exist"
        
        print(f"❌ {error_msg}")
        print(f"   Connection details: Host={os.getenv('DB_HOST')}, Port={os.getenv('DB_PORT')}, DB={os.getenv('DB_NAME')}, User={os.getenv('DB_USER')}")
        raise Exception("Database connection issue. Please try again.")
        
    except Exception as e:
        print(f"❌ Unexpected database error: {e}")
        print(f"   Connection details: Host={os.getenv('DB_HOST')}, Port={os.getenv('DB_PORT')}, DB={os.getenv('DB_NAME')}")
        raise Exception("Database connection issue. Please try again.")
