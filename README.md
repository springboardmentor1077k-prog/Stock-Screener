# 📈 AI Stock Screener

An intelligent, full-stack stock screening application that lets users query stock market data using **plain English**. The system uses a local LLM (via Ollama) to convert natural language queries into a structured DSL, which is compiled to SQL and executed against a MySQL database — all wrapped in a clean Streamlit UI with secure JWT authentication.

> **Developed by Surabhi & Sohan — Springboard Internship Project**

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| 🤖 **Natural Language Screening** | Query stocks in plain English — *"Tech stocks with PE < 20 and positive revenue"* |
| 🔄 **NL → DSL → SQL Pipeline** | LLM converts text to a validated DSL, which is compiled to optimized SQL |
| 🔐 **JWT Authentication** | Secure user registration, login, and protected routes via JSON Web Tokens |
| 📊 **Portfolio Management** | Create portfolios, add/remove holdings with auto-fetched market prices |
| 🔔 **Smart Alerts** | Set threshold-based alerts on any financial metric; evaluate on demand |
| ⚡ **Redis Caching** | Query results are cached to reduce LLM and database load |
| 🛡️ **Robust Error Handling** | Custom error hierarchy with retry logic and structured error responses |
| 📡 **Real-Time Data Ingestion** | Fetch fundamentals and financials from **Alpha Vantage** API |

---

## 🛠️ Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** — High-performance async REST API framework
- **[MySQL 8.0+](https://www.mysql.com/)** — Relational database for all financial and user data
- **[Ollama / Mistral](https://ollama.com/)** — Local LLM for natural language → DSL conversion
- **[Redis](https://redis.io/)** — In-memory caching for screener query results
- **[bcrypt](https://pypi.org/project/bcrypt/)** — Password hashing
- **[PyJWT](https://pyjwt.readthedocs.io/)** — JSON Web Token authentication
- **[mysql-connector-python](https://pypi.org/project/mysql-connector-python/)** — MySQL driver

### Frontend
- **[Streamlit](https://streamlit.io/)** — Interactive Python web UI
- **[requests](https://pypi.org/project/requests/)** — HTTP client to talk to the backend API

### DevOps & Tools
- **[Docker](https://www.docker.com/)** — Containerized Redis
- **[Uvicorn](https://www.uvicorn.org/)** — ASGI server for FastAPI
- **[Alpha Vantage API](https://www.alphavantage.co/)** — Free stock fundamentals data source

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER (Browser)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTP
┌──────────────────────────▼──────────────────────────────────┐
│              Streamlit Frontend (:8501)                     │
│   app.py | pages/_screener.py | _portfolio.py | _alerts.py  │
└──────────────────────────┬──────────────────────────────────┘
                           │  REST API (JWT in Header)
┌──────────────────────────▼──────────────────────────────────┐
│                FastAPI Backend (:8000)                      │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ /auth       │  │ /screener    │  │ /portfolios      │   │
│  │ /register   │  │ /screen      │  │ /alerts          │   │
│  │ /login      │  │              │  │ /stocks          │   │
│  └─────────────┘  └──────┬───────┘  └──────────────────┘   │
│                          │                                  │
│  ┌───────────────────────▼────────────────────────────┐     │
│  │              Screening Pipeline                    │     │
│  │  NL Query → LLM (Ollama) → DSL → Validator        │     │
│  │             → Rule Compiler → SQL → MySQL         │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────┬────────────────────────┬─────────────────────┘
               │                        │
┌──────────────▼──────┐   ┌─────────────▼────────────────────┐
│   MySQL DB (:3306)  │   │  Redis Cache (:6379)             │
│  stocks_master      │   │  Screener query results cache    │
│  fundamentals       │   └──────────────────────────────────┘
│  quarterly_financials│
│  analyst_targets    │
│  users              │
│  portfolios         │
│  portfolio_holdings │
│  alerts             │
└─────────────────────┘
        ▲
        │
┌───────┴──────────────────────────────────────────────────────┐
│         Ingestion Script (alphavantage_ingest.py)            │
│         Fetches data from Alpha Vantage API                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
Stock-Screener-Surabhi_Sohan/
│
├── README.md                         # ← You are here
├── DOCUMENTATION.md                  # Detailed technical documentation
├── API_REFERENCE.md                  # Full API reference
├── DATABASE_SETUP.md                 # Database schema & setup guide
├── dsl_output.json                   # Sample DSL output for reference
├── .gitignore                        # Git ignore rules
│
├── stock-ai-backend/                 # ── FastAPI Backend ──
│   ├── main.py                       # App entry point; all API route definitions
│   ├── screener_service.py           # Orchestrates NL → DSL → SQL → Result pipeline
│   ├── llm_integration.py            # Ollama/Mistral integration (NL → DSL)
│   ├── rule_compiler.py              # Compiles validated DSL into SQL queries
│   ├── validator.py                  # Validates DSL structure, fields, operators
│   ├── field_registry.py             # Central registry of all queryable DB fields
│   ├── alerts_service.py             # Alert creation, evaluation, and management
│   ├── auth_utils.py                 # JWT token creation/decoding, bcrypt hashing
│   ├── cache_utils.py                # Redis caching utility for screener results
│   ├── db.py                         # MySQL connection factory
│   ├── error_handlers.py             # Custom exceptions, retry logic, error formatting
│   ├── requirements.txt              # Backend Python dependencies
│   └── ingestion/
│       └── alphavantage_ingest.py    # Data ingestion from Alpha Vantage API
│
└── stock-ai-frontend/                # ── Streamlit Frontend ──
    ├── app.py                        # Main entry point (login/register + navigation)
    ├── api_client.py                 # Backend API wrapper (all HTTP calls)
    ├── config.py                     # Frontend configuration (API base URL, etc.)
    └── pages/
        ├── _screener.py              # Stock screener UI (natural language query)
        ├── _portfolio.py             # Portfolio management UI
        ├── _alerts.py                # Alerts management UI
        └── register.py               # User registration page
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python **3.10+**
- **MySQL Server** 8.0+
- **Ollama** with Mistral model installed
- **Redis** (via Docker recommended)
- **Alpha Vantage API Key** (free at [alphavantage.co](https://www.alphavantage.co/))

---

### Step 1 — Database Setup

Create a MySQL database and run the schema from `DATABASE_SETUP.md`:

```sql
CREATE DATABASE stock_screener;
```

Update credentials in `stock-ai-backend/db.py`:
```python
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="yourpassword",   # ← change this
        database="stock_screener"
    )
```

---

### Step 2 — Backend Setup

```bash
cd stock-ai-backend

# Install dependencies
pip install -r requirements.txt

# Start Redis (Docker)
docker run -d -p 6379:6379 --name redis-stock redis

# Run the backend server
uvicorn main:app --reload --port 8000
```

- **API Base**: `http://localhost:8000`
- **Interactive Docs (Swagger)**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

> ⚠️ The app works without Redis but caching will be disabled.

---

### Step 3 — Frontend Setup

```bash
cd stock-ai-frontend

# Install dependencies
pip install -r requirements.txt

# Run the UI
streamlit run app.py
```

Frontend opens at: **`http://localhost:8501`**

---

### Step 4 — AI (Ollama) Setup

```bash
# Start Ollama service
ollama serve

# Pull the Mistral model (first time only)
ollama pull mistral
```

---

### Step 5 — Data Ingestion (Optional)

To populate the database with real stock data from Alpha Vantage:

```bash
cd stock-ai-backend/ingestion
python alphavantage_ingest.py
```

> Set your Alpha Vantage API key in the ingestion script. Free tier has a rate limit of 5 requests/minute and 500/day.

---

## 📖 Usage Guide

### 1. Register & Login
- Open `http://localhost:8501`
- Click **Register** and create an account
- Login with your credentials to get a JWT token (stored in session)

### 2. Stock Screener
- Navigate to the **Screener** page
- Type a natural language query, for example:
  - *"Technology stocks with PE ratio less than 25"*
  - *"Stocks with debt below 1 billion and positive free cash flow"*
  - *"Healthcare stocks where revenue > 500 million"*
- Click **Run Screener** — results appear in a table

### 3. Portfolio Management
- Go to **Portfolio** page
- Create a new portfolio by entering a name
- Add stocks by entering the ticker symbol and quantity
- Market price is **auto-fetched** from the `analyst_targets` table
- Remove holdings as needed

### 4. Alerts
- Navigate to **Alerts** page
- Create an alert by selecting a metric (e.g., `pe_ratio`), operator (`<`, `>`, `=`), and threshold value
- Click **Evaluate Alerts** to check which conditions have been triggered

---

## 🔄 Query Processing Flow

```
User Input: "Show me tech stocks with PE ratio under 25"
      │
      ▼
[1] FastAPI /screener endpoint receives query
      │
      ▼
[2] llm_integration.py → sends prompt to Ollama/Mistral
      │
      ▼
[3] LLM returns structured DSL JSON:
    {
      "conditions": [
        {"field": "sector",   "operator": "=",  "value": "IT"},
        {"field": "pe_ratio", "operator": "<",  "value": 25}
      ]
    }
      │
      ▼
[4] validator.py → checks fields exist in field_registry, operators are valid
      │
      ▼
[5] rule_compiler.py → generates SQL:
    SELECT DISTINCT s.symbol, s.company_name
    FROM stocks_master s
    JOIN fundamentals f ON s.id = f.stock_id
    WHERE s.sector = 'IT' AND f.pe_ratio < 25
      │
      ▼
[6] Execute SQL against MySQL → return results to frontend
```

---

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/register` | ❌ | Register a new user |
| `POST` | `/login` | ❌ | Login and receive JWT `access_token` |

### Stock Screening

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/screen` | ✅ | Screen stocks with NL query (`{"text": "..."}`) |
| `POST` | `/screener` | ✅ | Same pipeline with richer error handling (`{"query": "..."}`) |
| `GET` | `/stocks` | ✅ | List all available stocks |

### Portfolio Management

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `GET` | `/portfolios` | ✅ | Get all user portfolios |
| `GET` | `/portfolios/{id}/holdings` | ✅ | Get all stocks in a portfolio |
| `POST` | `/portfolios/holdings` | ✅ | Add a stock (price auto-fetched) |
| `DELETE` | `/portfolios/holdings/{id}` | ✅ | Remove a stock holding |

### Alerts

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `GET` | `/alerts` | ✅ | List all user alerts |
| `POST` | `/alerts` | ✅ | Create a new metric-based alert |
| `POST` | `/alerts/evaluate` | ✅ | Trigger evaluation of all alerts |
| `DELETE` | `/alerts/{id}` | ✅ | Delete an alert |

All protected endpoints require the JWT token in the `Authorization` header:
```
Authorization: <your_jwt_token>
```

---

## 🗄️ Database Schema

| Table | Description |
|---|---|
| `users` | Registered users (email, hashed password) |
| `stocks_master` | Master list of stocks (symbol, company, sector, exchange) |
| `fundamentals` | PE ratio, PEG ratio, debt, free cash flow |
| `quarterly_financials` | Revenue, EBITDA, net profit per quarter/year |
| `analyst_targets` | Low/high target price and current market price |
| `portfolios` | Named portfolios per user |
| `portfolio_holdings` | Stocks in each portfolio (quantity, avg buy price) |
| `alerts` | User-defined metric threshold alerts |

For full SQL `CREATE TABLE` statements, see [DATABASE_SETUP.md](./DATABASE_SETUP.md).

---

## 📊 Supported Screener Fields

| Field Name | Source Table | Type | Example Query |
|---|---|---|---|
| `sector` | stocks_master | string | *"IT sector stocks"* |
| `exchange` | stocks_master | string | *"stocks on NASDAQ"* |
| `pe_ratio` | fundamentals | number | *"PE less than 25"* |
| `peg_ratio` | fundamentals | number | *"PEG ratio < 1"* |
| `debt` | fundamentals | number | *"debt below 1B"* |
| `free_cash_flow` | fundamentals | number | *"positive free cash flow"* |
| `revenue` | quarterly_financials | number | *"revenue > 500M"* |
| `ebitda` | quarterly_financials | number | *"EBITDA > 100M"* |
| `net_profit` | quarterly_financials | number | *"positive net profit"* |
| `target_price_low` | analyst_targets | number | *"low target > 100"* |
| `target_price_high` | analyst_targets | number | *"high target > 200"* |
| `current_market_price` | analyst_targets | number | *"price < 150"* |

---

## 🐛 Troubleshooting

| Issue | Solution |
|---|---|
| `Redis NOT reachable` | Run `docker start redis-stock` or install Redis locally. App works without it. |
| `Connection refused (port 8000)` | Make sure backend is running: `uvicorn main:app --reload --port 8000` |
| `Connection refused (port 3306)` | Ensure MySQL is running and credentials in `db.py` are correct |
| `Invalid or expired token` | Re-login to get a fresh JWT token |
| `Could not understand query` | Rephrase the query more simply, or check Ollama is running: `ollama serve` |
| `LF will be replaced by CRLF` | Git warning on Windows — safe to ignore, no action needed |
| `No stocks found` | Run the ingestion script to populate the database with stock data |

---

## 🔮 Future Enhancements

- [ ] Real-time WebSocket price updates
- [ ] Advanced charting with Plotly (price history, candlestick charts)
- [ ] Scheduled alert evaluation (cron job / background task)
- [ ] Multi-model LLM support (GPT-4, Gemini, Claude)
- [ ] Export screener results to CSV/Excel
- [ ] Watchlist feature alongside portfolios
- [ ] Admin dashboard for data management

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

---

**Developed for Springboard Internship — Surabhi & Sohan © 2025**