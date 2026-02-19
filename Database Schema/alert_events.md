# alert_events

## Columns
- id INTEGER PRIMARY KEY AUTOINCREMENT
- alert_id INTEGER NOT NULL
- stock_id TEXT NOT NULL
- triggered_value REAL NOT NULL
- triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP

## Description
- Records each alert firing instance with the observed value.
- Enables audit trail and prevents duplicate notifications when logic enforces fire-once.

## Relationships
- alert_id → alerts.id
- stock_id → stocks.symbol

