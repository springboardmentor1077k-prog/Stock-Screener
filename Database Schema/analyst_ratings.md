# analyst_ratings

## Columns
- symbol TEXT PRIMARY KEY
- target_price REAL
- recommendation TEXT
- disclaimer TEXT

## Description
- Optional analyst context per stock.
- Used for display or supplemental filtering in future features.

## Relationships
- symbol → stocks.symbol

