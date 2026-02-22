import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import redis

redis_client = redis.Redis(host='localhost',port=6379,db=0,decode_responses=True,socket_timeout=1,socket_connect_timeout=1)

try:
    redis_client.ping()
    print('connected to redis!')
except Exception as e:
    print("Redis is OFFLINE. Caching is disabled, but the app will still run.")

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Load Secrets from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("❌ DATABASE_URL not found in .env file")
    raise ValueError("DATABASE_URL is missing! Check your .env file.")

# 3. Create Database Engine with Connection Pooling
# pool_pre_ping=True: Checks if the DB is alive before trying to use it.
# pool_size=10: Keeps 10 connections open and ready.
# max_overflow=20: Allows 20 extra connections during traffic spikes.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True, 
    pool_size=10,       
    max_overflow=20     
)

# 4. Create Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Base Class for Models
Base = declarative_base()

def init_db():
    """Creates tables if they don't exist."""
    from . import models
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables initialized successfully.")
