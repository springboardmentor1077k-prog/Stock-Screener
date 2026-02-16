# AI-Powered Mobile Stock Screener and Advisory Platform

A full-stack stock screening and portfolio platform with natural-language queries, JWT auth, portfolio tracking, price alerts, and an AI investment advisor. The backend is FastAPI; the frontend is Streamlit with a dark-themed UI.

---

## Features

- **Natural-language stock screening** — Query in plain English (e.g. “PE below 30”, “IT stocks with high growth”); DSL compiler + SQL engine return matching stocks with fundamentals.
- **Portfolio management** — Add holdings by symbol (quantity, avg price); view portfolio with current prices and total value; summary with total value and return.
- **Price alerts** — Create alerts by symbol/condition (above/below price); list and manage active alerts.
- **AI Stock Advisor** — Chat-style Q&A for investment questions (risk, sectors, valuation) powered by OpenAI.
- **Market data** — Alpha Vantage integration for company overview, fundamentals, and income statements; optional bulk ingestion script for many symbols (respects free-tier rate limits).
- **Authentication** — Register, login, JWT access + refresh tokens; protected API and frontend routes.
- **Database** — SQLite by default (`stock_screener.db`); can switch to PostgreSQL via `DATABASE_URL`.

---

## Project structure

```
├── backend/                 # FastAPI app
│   ├── api/routers/         # Auth, screener, portfolio, alerts, data, analytics, AI advice
│   ├── auth/                # JWT handling
│   ├── core/                # Config, utils, exceptions
│   ├── database/            # Connection, session
│   ├── models/              # SQLAlchemy models, Pydantic schemas
│   └── services/            # Screener engine, portfolio, alerts, data ingestion/fetcher
├── frontend/
│   └── streamlit_app.py     # Main Streamlit UI (Screener, Portfolio, Alerts, AI Advisor)
├── ai_layer/
    |-- llm_parser_service.py              # LLM parser (NLP → DSL)
├── config/
│   ├── .env                 # Your secrets (not committed)
│   ├── .env.example         # Template for env vars
│   └── requirements.txt
├── scripts/
│   ├── run_backend.py       # Start API (port 8002)
│   ├── run_frontend.py      # Start Streamlit (port 8501)
│   ├── init_db.py           # Create DB tables
│   ├── ingest_sample_stocks.py   # Bulk ingest from Alpha Vantage
│   ├── seed_local_sample_data.py # Seed a few sample stocks
│   └── debug_db_snapshot.py      # Print DB row counts/samples
├── stock_screener.db        # SQLite DB (create with init_db + ingest/import)
└── README.md
```

---

## Prerequisites

- **Python 3.10+**
- **Environment file** — Copy `config/.env.example` to `config/.env` and fill in keys (see below).

Optional for full functionality:

- **OpenAI API key** — For AI Advisor.
- **Alpha Vantage API key** — For live fundamentals and bulk ingestion (free tier: 25 requests/day, 5/min).

---

## Installation

1. **Clone and enter the project**
   ```bash
   git clone <repository-url>
   cd "AI-Powered Mobile Stock Screener and Advisory Platform"
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r config/requirements.txt
   ```

4. **Environment variables**  
   Copy the example and edit with your values:
   ```bash
   cp config/.env.example config/.env
   ```
   Edit `config/.env`. Minimum for local run with SQLite:

   ```env
   # Database (default: SQLite in project root)
   DATABASE_URL=sqlite:///./stock_screener.db

   # JWT
   SECRET_KEY=your-very-long-random-secret-key-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Optional: OpenAI (for AI Advisor)
   OPENAI_API_KEY=sk-your-openai-key

   # Optional: Alpha Vantage (for market data & ingestion)
   ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
   ```

5. **Initialize the database**
   ```bash
   python scripts/init_db.py
   ```

6. **Load stock data (choose one or both)**
   - **From Alpha Vantage** (uses API quota):
     ```bash
     python scripts/ingest_sample_stocks.py
     ```
     Default: 12 symbols/run (INGEST_MAX_SYMBOLS=12). Set `INGEST_MAX_SYMBOLS=172` to attempt full list (will hit free-tier limit after ~12).
   - **From existing DB** (e.g. Bhavik_Mittal branch DB):
     ```bash
     python scripts/import_from_bhavik_db.py
     ```
     Reads `Stock-Screener/analyst_demo/stocks.db` and writes into `stock_screener.db`.

---

## Running the application

**Terminal 1 — Backend**
```bash
python scripts/run_backend.py
```
- API: `http://localhost:8002`
- Docs: `http://localhost:8002/docs`

**Terminal 2 — Frontend**
```bash
python scripts/run_frontend.py
```
- App: `http://localhost:8501`

The Streamlit app expects the backend at **port 8002**. Register or log in, then use Screener, Portfolio, Alerts, and AI Advisor.

---

## Main API endpoints

| Area        | Method | Endpoint | Description |
|------------|--------|----------|-------------|
| Auth       | POST   | `/api/v1/auth/register` | Register |
| Auth       | POST   | `/api/v1/auth/login`   | Login |
| Auth       | POST   | `/api/v1/auth/refresh` | Refresh token |
| Screener   | POST   | `/api/v1/screener/screen` | Run screener (query, sector, etc.) |
| Portfolio  | GET    | `/api/v1/portfolio/`   | Get holdings |
| Portfolio  | POST   | `/api/v1/portfolio/add-by-symbol` | Add holding by symbol |
| Portfolio  | GET    | `/api/v1/portfolio/summary` | Total value, return |
| Alerts     | GET    | `/api/v1/alerts/`      | List alerts |
| Alerts     | POST   | `/api/v1/alerts/create`| Create alert |
| Data       | POST   | `/api/v1/data/ingest/stock` | Ingest one symbol |
| Data       | POST   | `/api/v1/data/ingest/bulk`  | Ingest many symbols |
| AI         | POST   | `/api/v1/ai-advice`    | AI investment advice |

---

## Tech stack

- **Backend:** FastAPI, SQLAlchemy 2, Pydantic, JWT (python-jose), bcrypt
- **Frontend:** Streamlit (dark UI, responsive layout)
- **Database:** SQLite (default) or PostgreSQL
- **APIs:** Alpha Vantage (market data), OpenAI (AI Advisor)
- **Security:** CORS, trusted-host middleware, security headers, input sanitization

---

## Security notes

- Do not commit `config/.env` or any file containing API keys or `SECRET_KEY`.
- Use a strong, random `SECRET_KEY` in production.
- Passwords are hashed with bcrypt; queries use parameterized SQL.

---
