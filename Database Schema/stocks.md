# stocks

## Columns
- symbol TEXT PRIMARY KEY
- company_name TEXT
- sector TEXT
- price REAL
- market_cap REAL
- pe_ratio REAL

## Description
- Master reference of tradable equities.
- market_cap stored in Billions.
- Used by the screener and portfolio joins.

## Relationships
- Referenced by portfolio_holdings.stock_id → stocks.symbol
- Referenced by alert_events.stock_id → stocks.symbol
- Referenced by analyst_ratings.symbol → stocks.symbol

