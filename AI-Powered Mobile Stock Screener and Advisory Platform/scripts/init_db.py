#!/usr/bin/env python3
"""
Database Initialization Script
Creates all required tables in the database
"""

import sys
from pathlib import Path

# Add the project root to the Python path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from backend.database.connection import engine
from backend.models.database import Base

# Load environment variables
env_path = project_root / "config" / ".env"
load_dotenv(dotenv_path=env_path)

def init_db():
    """Initialize the database by creating all tables"""
    print("Initializing database...")
    print("Creating tables...")
    
    # Create all tables defined in the models
    Base.metadata.create_all(bind=engine)
    
    print("Database initialized successfully!")
    print("All tables have been created.")

if __name__ == "__main__":
    init_db()