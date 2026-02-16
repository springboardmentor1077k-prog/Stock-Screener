# Database Connection Module
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

# Database URL - in production, use environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stock_screener.db")

# Configure the engine with connection pooling and timeout settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite doesn't support connection pooling or timeout settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # Required for SQLite with threading
    )
else:
    # For PostgreSQL, use connection pooling
    from sqlalchemy.pool import QueuePool
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,  # Number of connection to maintain
        max_overflow=10,  # Number of connections beyond pool_size
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,  # Recycle connections after 5 minutes
        connect_args={
            "connect_timeout": 10,  # Timeout for establishing connection (in seconds)
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Log the error for debugging but don't expose internal details to the caller
        logger.error(f"Database session error: {str(e)}", exc_info=True)
        # We don't re-raise the exception here to avoid exposing internal errors
        # The calling function will handle the error appropriately
        db.rollback()
        raise
    finally:
        db.close()
