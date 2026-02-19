# Database Schema Overview

## Tables
- stocks
- portfolios
- portfolio_holdings
- alerts
- alert_events
- analyst_ratings

## Relationships
- portfolios (1) —— (N) portfolio_holdings
  - portfolio_holdings.portfolio_id → portfolios.id
- stocks (1) —— (N) portfolio_holdings
  - portfolio_holdings.stock_id → stocks.symbol
- portfolios (1) —— (N) alerts
  - alerts.portfolio_id → portfolios.id
- alerts (1) —— (N) alert_events
  - alert_events.alert_id → alerts.id
- stocks (1) —— (1) analyst_ratings
  - analyst_ratings.symbol → stocks.symbol

## Notes
- market_cap in stocks is stored in Billions (e.g., 2.5 = $2.5B)
- Natural language screener queries act on the stocks table and apply WHERE conditions
- Profit/Loss in portfolio results is computed from portfolio_holdings joined with stocks.price

