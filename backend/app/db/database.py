from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import time

DATABASE_URL = settings.DATABASE_URL

engine = None

# Retry DB connection (important in Docker)
for i in range(10):
    try:
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        conn.close()
        print("✅ Database connected successfully")
        break
    except Exception:
        print("⏳ Waiting for database to be ready...")
        time.sleep(3)
else:
    raise Exception("❌ Could not connect to the database")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()