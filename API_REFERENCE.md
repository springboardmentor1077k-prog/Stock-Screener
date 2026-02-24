# API Quick Reference

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Login
**POST** `/login`

```json
// Request
{
  "email": "admin@test.com",
  "password": "admin123"
}

// Response (200)
{
  "access_token": "550e8400-e29b-41d4-a716-446655440000"
}

// Error (401)
{
  "detail": "Invalid credentials"
}
```

### 2. Screen Stocks
**POST** `/screen`

**Headers**: `Authorization: <token>`

```json
// Request
{
  "text": "Stocks with PE ratio less than 25"
}

// Response (200)
{
  "status": "success",
  "count": 15,
  "rows": [
    {
      "symbol": "AAPL",
      "company_name": "Apple Inc."
    }
  ]
}

// Error (400)
{
  "detail": "Unsupported Query"
}
```

## Query Examples

| Query | Description |
|-------|-------------|
| `Stocks with PE ratio less than 25` | Basic PE filter |
| `Technology stocks` | Sector filter |
| `Stocks with positive net profit` | Financial filter |
| `Low debt and high free cash flow` | Multiple conditions |

## Supported Fields

### stocks_master
- `symbol`, `company_name`, `sector`, `exchange`

### fundamentals
- `pe_ratio`, `peg_ratio`, `debt`, `free_cash_flow`

### quarterly_financials
- `revenue`, `ebitda`, `net_profit`

### analyst_targets
- `target_price_low`, `target_price_high`, `current_market_price`

## Supported Operators
- `<` (less than)
- `>` (greater than)
- `=` (equal to)
- `<=` (less than or equal)
- `>=` (greater than or equal)

## Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
