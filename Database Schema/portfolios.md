# portfolios

## Columns
- id INTEGER PRIMARY KEY AUTOINCREMENT
- user_id INTEGER NOT NULL
- name TEXT NOT NULL
- created_at DATETIME DEFAULT CURRENT_TIMESTAMP

## Description
- Logical grouping of holdings per user.
- Demo assumes `id = 1` exists or is created.

## Relationships
- One-to-many with portfolio_holdings via portfolio_id
- One-to-many with alerts via portfolio_id

