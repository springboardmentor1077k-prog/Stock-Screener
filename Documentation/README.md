# Stock Screener App — Documentation

## Overview
This project is a full-stack stock screening dashboard with a Streamlit frontend and a Flask backend connected to an SQLite database. It supports both rule-based filters and natural language (sentence) queries, provides portfolio views with computed profit/loss, and includes alert creation and retrieval.

- Frontend: Streamlit multi-page dashboard
- Backend: Flask API with SQLite
- Natural language to SQL: Rule-based AI engine for demo stability
- Centralized API utility: Shared GET/POST/error handling for all screens
- Robust UI states: Loading, success, empty, error

## Tech Stack
- Python 3.11+
- Streamlit (UI)
- Flask (API server)
- SQLite (data)
- Requests, Pandas

## Architecture & Flow
- Input UI → Backend validation
- DSL/NLP creation (natural language understood by AI engine)
- SQL execution against SQLite
- Business logic (filters, joins, profit/loss calculations)
- Error handling:
  - Backend returns JSON error contract: `{"error_code": "...", "message": "..."}` on failure
  - Frontend displays the message and state accordingly

## Directory Layout
- Streamlit frontend: [app.py](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/Streamlit_Dashboard/app.py)
- Backend server: [server.py](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/Streamlit_Dashboard/server.py)
- Centralized API utils: [api.py](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/Streamlit_Dashboard/utils/api.py)
- AI service (NLP→SQL): [ai_service.py](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/Streamlit_Dashboard/ai_service.py)
- Tables and DB config: [tables](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/tables/)

## Backend API
- Base URL: `http://localhost:5000`

### 1) Screener — POST /screen
- Purpose: Screen stocks by filters or natural language sentence queries.
- Request payload:
```json
{
  "query": "Show IT stocks with pe ratio below 20",
  "sector": "IT",
  "strong_only": true,
  "market_cap": "Large Cap (>10B)"
}
```
- Success response:
```json
{ "status": "success", "data": [ /* rows from stocks */ ] }
```
- Error response:
```json
{ "error_code": "invalid_query", "message": "unsupported query format" }
```
- Notes:
  - Numeric queries like `"50"` map to `(price > 50 OR pe_ratio < 50)`.
  - Natural language queries are parsed by AIBackend to SQL WHERE clauses.
  - Market cap is stored in Billions (e.g., 10 means ~$10B).

### 2) Portfolio — GET /portfolio
- Purpose: Return holdings joined with current prices and compute profit/loss.
- Success response:
```json
{
  "status": "success",
  "data": [
    {
      "symbol": "AAPL",
      "quantity": 10,
      "avg_buy_price": 150.0,
      "current_price": 185.5,
      "company_name": "Apple Inc.",
      "profit_loss": 355.0
    }
  ]
}
```
- Error response:
```json
{ "error_code": "server_error", "message": "..." }
```

### 3) Alerts
- GET /alerts — list alerts for the demo portfolio
- POST /alerts — create a price alert
- POST /alerts/checks — placeholder endpoint for alert processing
- Create alert request:
```json
{ "symbol": "AAPL", "condition": "Above Price", "value": 150 }
```
- Success response:
```json
{ "status": "success", "message": "Alert created" }
```
- Error response:
```json
{ "error_code": "creation_error", "message": "..." }
```

## Data Model
- DB path configured via [config.py](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/tables/config.py) or fallback `analyst_demo/stocks.db`.
- Tables:
  - stocks: `symbol`, `company_name`, `sector`, `price`, `market_cap` (Billions), `pe_ratio`, `change`
  - portfolios: `id`, `user_id`, `name`, `created_at`
  - portfolio_holdings: `id`, `portfolio_id`, `stock_id`, `quantity`, `avg_buy_price`, `created_at`, `updated_at`
  - alerts: `id`, `user_id`, `portfolio_id`, `metric`, `operator`, `threshold`, `is_active`, `created_at`
- Schemas defined in the [tables](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/tables/) modules.

## Frontend UI
- Pages:
  - Screener: query input, sector, strong-only checkbox, market-cap filter, results table
  - Portfolio: holdings table, computed totals (current value and profit/loss)
  - Alerts: alert creation form and active alerts list
- Components used:
  - `st.container`, `st.columns`, `st.selectbox`, `st.checkbox`, `st.spinner`, `st.dataframe`, `st.session_state`, `st.sidebar`, `st.form`
- State management:
  - Loading state with `st.spinner` for API calls
  - Success with data tables and metrics
  - Empty state with informative messages
  - Error state using backend error contract

## Centralized API Utility
- File: [api.py](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/Streamlit_Dashboard/utils/api.py)
- Functions:
  - `fetch_data(endpoint, params=None)` — GET requests
  - `post_data(endpoint, payload)` — POST requests
  - `_handle_response(response)` — parses JSON and preserves backend error codes/messages
- Usage in [app.py](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/Streamlit_Dashboard/app.py):
  - Screener uses `post_data("screen", payload)`
  - Portfolio uses `fetch_data("portfolio")`
  - Alerts uses `fetch_data("alerts")` and `post_data("alerts", payload)`

## Setup & Run
- Install dependencies:
```
pip install streamlit flask requests pandas
```
- Start backend:
```
python Stock-Screener/Streamlit_Dashboard/server.py
```
- Start frontend:
```
streamlit run "Stock-Screener/Streamlit_Dashboard/app.py"
```
- Access UI: `http://localhost:8501`

## Natural Language Query Support
- Implemented by [ai_service.py](file:///c:/Users/Lenovo/Desktop/Stock%20screener%20app%20(Project)/Stock-Screener/Streamlit_Dashboard/ai_service.py)
- Examples:
  - "Show IT sector stocks with price greater than 200"
  - "Find finance sector stocks where pe ratio is less than 15"
  - "stocks with market cap above 50"
- Limitations:
  - Rule-based parser; supports common phrases and simple comparisons
  - Returns `{"error_code": "invalid_query", "message": "..."}` for unsupported patterns

## Error Contract & Handling
- Backend failure:
  - Example: `{"error_code": "server_error", "message": "..."}` with HTTP 500
  - UI shows `st.error("Error (server_error): ...")`
- Invalid query:
  - Example: `{"error_code": "invalid_query", "message": "unsupported query format"}`
  - UI shows descriptive error with guidance
- Network error:
  - Captured in API util as `{"error_code": "network_error", "message": "Server not reachable: ..."}` 

## Troubleshooting
- "Server not reachable":
  - Ensure Flask server is running on port 5000
  - Check firewall or conflicting ports
- "No matching stocks":
  - Adjust filters or confirm sector labels match DB (e.g., "IT")
  - Market cap is in Billions (e.g., 10 for ~$10B)
- "Invalid JSON response":
  - Ensure backend returns valid JSON; API util guards parsing errors

## Security & Best Practices
- Do not log secrets or credentials
- Validate all inputs server-side
- Avoid SQL injection; use parameterized queries in filter path
- Demo AI SQL generation embeds numbers; safe in controlled phrases

## Testing Ideas
- Unit tests for:
  - NLP-to-SQL generation on common phrases
  - API endpoints return schema-compliant JSON
  - Portfolio profit/loss calculations
- Integration tests:
  - Frontend–backend round trips for all screens

## Demos (Functional Expectations)
- Portfolio demo:
  - Loads current prices, computes profit/loss, shows friendly success when data loads without dummy data
- Alerts demo:
  - Create alerts and list them; checks endpoint is present for future “fire-once” processing with clear messages
- Edge cases:
  - If alert condition remains true after firing, system should record once and not repeatedly notify (to be implemented in alerts/checks logic)

