#!/usr/bin/env python3
"""
Frontend startup script for AI-Powered Stock Screener
"""
import subprocess
import sys
import os
from pathlib import Path

# Add the project root to the Python path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables from config directory
env_path = project_root / "config" / ".env"
load_dotenv(dotenv_path=env_path)

def main():
    print("Starting AI-Powered Stock Screener Frontend...")
    print("Ensure the backend is running on http://localhost:8000")
    print("The Streamlit app will be available in your browser")
    
    # Change to project root directory before running streamlit
    os.chdir(project_root)
    
    subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py", "--server.port", "8501"])

if __name__ == "__main__":
    main()