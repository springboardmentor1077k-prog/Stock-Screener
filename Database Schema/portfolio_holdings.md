# portfolio_holdings

## Columns
- id INTEGER PRIMARY KEY AUTOINCREMENT
- portfolio_id INTEGER NOT NULL
- stock_id TEXT NOT NULL
- quantity REAL NOT NULL
- avg_buy_price REAL NOT NULL
- created_at DATETIME DEFAULT CURRENT_TIMESTAMP
- updated_at DATETIME DEFAULT CURRENT_TIMESTAMP

## Description
- Holdings entries within a portfolio.
- Joined with stocks to compute current_price and profit_loss.

## Relationships
- portfolio_id → portfolios.id
- stock_id → stocks.symbol

