# screener (logical)

## Description
- The screener is not a database table. It is a logical service backed by the stocks table.
- It accepts rule-based filters and natural language queries, translates them to SQL, and returns rows from stocks.

## Input Sources
- Filters: sector, strong_only (heuristic), market_cap bands
- Natural language: phrases like "price greater than 100", "pe ratio below 15", "IT sector"

## Output
- Selected columns from stocks: symbol, company_name, sector, price, market_cap, pe_ratio

## Notes
- Numeric queries "50" map to `(price > 50 OR pe_ratio < 50)`.
- Market cap comparisons use Billions.
- AI engine is rule-based for demo stability.

