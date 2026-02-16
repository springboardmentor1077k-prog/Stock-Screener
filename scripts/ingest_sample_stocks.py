#!/usr/bin/env python3
"""
Sample data ingestion script.

This script populates the local `stock_screener.db` database with a small set
of real stocks and their fundamentals/quarterly data using the existing
Alpha Vantage based data ingestion pipeline.

Usage:
    python scripts/ingest_sample_stocks.py

Requirements:
    - Set ALPHA_VANTAGE_API_KEY in `config/.env`
    - Backend dependencies installed (see config/requirements.txt)
"""

import os
import sys
from pathlib import Path

# Ensure project root is on the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables (including ALPHA_VANTAGE_API_KEY)
env_path = project_root / "config" / ".env"
load_dotenv(dotenv_path=env_path)

from backend.database.connection import SessionLocal
from backend.services.data_ingestion_service import data_ingestion_service


def main():
    # Free tier = 25 requests/day, 5/min. ~2 calls per symbol => ~12 symbols/day per run.
    max_per_run = int(os.getenv("INGEST_MAX_SYMBOLS", "12"))
    print("Starting sample stock data ingestion...")
    print("NOTE: Alpha Vantage FREE tier = 25 requests/day and 5/min (~12 symbols/day).")
    print("Set INGEST_MAX_SYMBOLS=172 to attempt all (will hit daily limit after ~12).")
    print("Make sure ALPHA_VANTAGE_API_KEY is set in config/.env.\n")

    # ~200 real, liquid US tickers across sectors (S&P 500 style universe)
    symbols = [
        # Mega-cap tech / communication
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "NVDA", "AVGO",
        "ADBE", "CRM", "CSCO", "INTC", "AMD", "ORCL", "IBM", "QCOM", "TXN", "MU",
        "NFLX", "INTU", "NOW", "SHOP", "UBER", "LYFT",

        # Financials
        "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "COF",
        "PNC", "USB", "TFC", "BK", "AIG", "MET", "PRU", "CB",

        # Healthcare
        "JNJ", "PFE", "MRK", "ABBV", "TMO", "ABT", "LLY", "BMY", "AMGN", "GILD",
        "CVS", "UNH", "CI", "HUM", "ISRG", "MDT", "SYK",

        # Consumer staples
        "PG", "KO", "PEP", "WMT", "COST", "MO", "PM", "CL", "KMB", "MDLZ",
        "TGT", "KR",

        # Consumer discretionary
        "HD", "LOW", "NKE", "SBUX", "MCD", "DG", "DLTR", "ROST", "TJX", "BKNG",
        "MAR", "F", "GM", "RIVN",

        # Energy
        "XOM", "CVX", "COP", "SLB", "EOG", "PXD", "PSX", "MPC", "VLO", "HAL",

        # Industrials
        "BA", "GE", "CAT", "DE", "UPS", "FDX", "LMT", "RTX", "HON", "MMM",
        "ETN", "EMR", "GD", "NOC", "UNP", "CSX", "NSC",

        # Materials
        "LIN", "APD", "SHW", "ECL", "NEM", "FCX", "ALB", "IFF", "DOW",

        # Utilities
        "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "PEG",

        # Real estate
        "PLD", "AMT", "CCI", "EQIX", "SPG", "O", "PSA", "AVB", "EQR",

        # More tech / growth
        "SNOW", "ZS", "CRWD", "OKTA", "NET", "DOCU", "TEAM", "MDB", "DDOG", "PANW",
        "ZM", "ROKU", "TWLO", "SQ", "PYPL", "FSLY",

        # Semiconductors
        "ASML", "ADI", "KLAC", "LRCX", "NXPI", "MCHP", "ON", "MRVL",

        # Telecom
        "T", "VZ", "TMUS",

        # Other large caps
        "BRK.B", "BRK.A", "SPY", "QQQ", "DIA",
    ]

    symbols = symbols[:max_per_run]
    print(f"Ingesting up to {len(symbols)} symbols this run (INGEST_MAX_SYMBOLS={max_per_run}).\n")

    db = SessionLocal()
    results = {}
    try:
        for i, symbol in enumerate(symbols, 1):
            if i % 5 == 1 or i == len(symbols):
                print(f"  Progress: {i}/{len(symbols)} ...")
            results[symbol] = data_ingestion_service.ingest_stock_data(db, symbol)
            if i == 1 and not results[symbol]:
                print(
                    "\n*** First symbol failed. If logs above say 'rate limit' or 'daily quota', "
                    "your 25/day limit is likely used. Run again tomorrow or set INGEST_MAX_SYMBOLS=12 and run once per day.\n"
                )
    finally:
        db.close()

    ok_count = sum(1 for v in results.values() if v)
    print(f"\nIngestion results ({ok_count}/{len(symbols)} succeeded):")
    for sym, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {sym}: {status}")

    print("\nDone. You can now use the Screener and Portfolio pages with real data.")


if __name__ == "__main__":
    main()

