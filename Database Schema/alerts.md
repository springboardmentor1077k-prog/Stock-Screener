# alerts

## Columns
- id INTEGER PRIMARY KEY AUTOINCREMENT
- user_id INTEGER NOT NULL
- portfolio_id INTEGER NOT NULL
- metric TEXT NOT NULL
- operator TEXT NOT NULL
- threshold REAL NOT NULL
- is_active BOOLEAN DEFAULT 1
- created_at DATETIME DEFAULT CURRENT_TIMESTAMP

## Description
- User-defined alert rules (e.g., "AAPL price > 150").
- Demo stores `metric` as a string including symbol context (e.g., "AAPL price").

## Relationships
- portfolio_id → portfolios.id
- Referenced by alert_events.alert_id → alerts.id

