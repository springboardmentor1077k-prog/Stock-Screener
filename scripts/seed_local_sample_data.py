#!/usr/bin/env python3
"""
Seed local sample stock data directly into `stock_screener.db`.

This script does NOT call any external APIs or require API keys.
It simply inserts a few example stocks and fundamentals so that:
  - The Screener has data to work with
  - The Portfolio "add-by-symbol" flow can find symbols like AAPL/MSFT/TSLA

Usage:
    python scripts/init_db.py              # ensure tables exist
    python scripts/seed_local_sample_data.py
"""

import sys
from pathlib import Path
from decimal import Decimal

# Ensure project root is on the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.models.database import MasterStock, Fundamental


def upsert_stock(session, symbol: str, company_name: str, exchange: str, sector: str, industry: str):
    symbol = symbol.upper()
    stock = session.query(MasterStock).filter(MasterStock.symbol == symbol).first()
    if stock:
        stock.company_name = company_name
        stock.exchange = exchange
        stock.sector = sector
        stock.industry = industry
    else:
        stock = MasterStock(
            symbol=symbol,
            company_name=company_name,
            exchange=exchange,
            sector=sector,
            industry=industry,
        )
        session.add(stock)
        session.flush()  # assign stock_id
    return stock


def upsert_fundamental(
    session,
    stock_id: str,
    *,
    pe_ratio: float,
    peg_ratio: float | None = None,
    ebitda: float | None = None,
    free_cash_flow: float | None = None,
    dividend_yield: float | None = None,
    market_cap: float | None = None,
    current_price: float | None = None,
):
    fundamental = session.query(Fundamental).filter(Fundamental.stock_id == stock_id).first()
    fields = dict(
        pe_ratio=Decimal(str(pe_ratio)),
        peg_ratio=Decimal(str(peg_ratio)) if peg_ratio is not None else None,
        ebitda=Decimal(str(ebitda)) if ebitda is not None else None,
        free_cash_flow=Decimal(str(free_cash_flow)) if free_cash_flow is not None else None,
        dividend_yield=Decimal(str(dividend_yield)) if dividend_yield is not None else None,
        market_cap=Decimal(str(market_cap)) if market_cap is not None else None,
        current_price=Decimal(str(current_price)) if current_price is not None else None,
    )

    if fundamental:
        for k, v in fields.items():
            setattr(fundamental, k, v)
    else:
        fundamental = Fundamental(stock_id=stock_id, **fields, last_updated_date=None)
        session.add(fundamental)


def main():
    session = SessionLocal()
    try:
        # Example large-cap tech + growth names with reasonable fundamentals
        examples = [
            # symbol, company_name, exchange, sector, industry, pe, peg, fcf, div_yield, mcap, price
            ("AAPL", "Apple Inc.", "NASDAQ", "Information Technology", "Consumer Electronics", 28.5, 2.1, 600_000_000_000, 0.6, 2_900_000_000_000, 190.0),
            ("MSFT", "Microsoft Corporation", "NASDAQ", "Information Technology", "Systems Software", 31.2, 2.0, 650_000_000_000, 0.8, 3_000_000_000_000, 410.0),
            ("TSLA", "Tesla, Inc.", "NASDAQ", "Consumer Discretionary", "Automobiles", 65.0, 1.5, 20_000_000_000, 0.0, 800_000_000_000, 250.0),
        ]

        for sym, name, exch, sector, industry, pe, peg, fcf, div_y, mcap, price in examples:
            stock = upsert_stock(session, sym, name, exch, sector, industry)
            upsert_fundamental(
                session,
                stock.stock_id,
                pe_ratio=pe,
                peg_ratio=peg,
                free_cash_flow=fcf,
                dividend_yield=div_y,
                market_cap=mcap,
                current_price=price,
            )

        session.commit()
        print("Seeded local sample data for: AAPL, MSFT, TSLA")
    finally:
        session.close()


if __name__ == "__main__":
    main()

