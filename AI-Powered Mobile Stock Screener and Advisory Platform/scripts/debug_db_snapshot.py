#!/usr/bin/env python3
"""
Quick DB snapshot helper.

Prints how many stocks and fundamentals exist in the current DATABASE_URL,
and shows a few sample rows. This is useful to verify that ingestion scripts
have actually populated data beyond the local seed (e.g. only AAPL).

Usage:
    python scripts/debug_db_snapshot.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.models.database import MasterStock, Fundamental


def main():
    session = SessionLocal()
    try:
        stock_count = session.query(MasterStock).count()
        fundamental_count = session.query(Fundamental).count()

        print(f"MasterStock rows:    {stock_count}")
        print(f"Fundamental rows:    {fundamental_count}")
        print("")

        print("Sample MasterStock rows:")
        for stock in session.query(MasterStock).order_by(MasterStock.symbol).limit(10):
            print(f"  {stock.symbol} | {stock.company_name} | {stock.exchange} | sector={stock.sector}")

        print("\nSample Fundamental rows:")
        for f in session.query(Fundamental).limit(10):
            print(
                f"  stock_id={f.stock_id} | PE={f.pe_ratio} | Price={f.current_price} | MC={f.market_cap}"
            )
    finally:
        session.close()


if __name__ == "__main__":
    main()

