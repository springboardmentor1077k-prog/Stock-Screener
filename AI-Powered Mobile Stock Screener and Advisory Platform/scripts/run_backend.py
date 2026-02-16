#!/usr/bin/env python3
"""
Backend startup script for AI-Powered Stock Screener
"""
import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to the Python path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables from config directory
env_path = project_root / "config" / ".env"
load_dotenv(dotenv_path=env_path)

def main():
    print("Starting AI-Powered Stock Screener Backend...")
    print("Ensure you have set up your .env file with the required configurations")
    print("Visit http://localhost:8002/docs for API documentation")
    
    # Change to project root directory before running uvicorn
    os.chdir(project_root)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()