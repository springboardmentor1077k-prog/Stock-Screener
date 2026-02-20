# 📈 ProTrade AI - Stock Screener Platform

An intelligent stock screening and portfolio management platform that uses **Natural Language Processing** to convert plain English queries into sophisticated stock filters, with real-time alerts, analyst insights, and compliance features.

## 🎯 Features

### Core Functionality
- **AI-Powered Screener** 🔍
  - Convert natural language to SQL: *"Show undervalued tech stocks with PE < 20"*
  - Support for complex queries with AND/OR logic
  - Filter by sector, P/E ratio, PEG ratio, dividend yield, debt-to-equity
  - Quarterly financial analysis (revenue, net profit, EBITDA trends)

- **Portfolio Management** 💼
  - Track personal stock holdings
  - Real-time P/L calculations
  - Performance analytics

- **Smart Alerts System** 🔔
  - Create custom price/metric alerts
  - Background scheduler for periodic checks
  - Real-time notifications when triggered
  - One-time trigger logic to prevent duplicates

- **Analyst Insights** 🎯
  - AI-generated market analysis reports
  - Analyst target price recommendations
  - Upside/downside calculations
  - Sector-wide trends

- **Compliance & Safety** ⚖️
  - Educational disclaimer system
  - Advisory keyword filtering
  - Safe error handling (no stack traces exposed)
  - User authentication with JWT tokens

## 🏗️ Architecture

```
Frontend Layer:
  └─ Streamlit UI (streamlit_app.py)

API Layer (FastAPI):
  └─ main.py (Core endpoints)
      ├─ /signup, /login (Auth)
      ├─ /screen (NL Query Processing)
      ├─ /portfolio (Holdings)
      ├─ /alerts (Alert Management)
      └─ /notifications (Real-time Alerts)

Processing Layer:
  ├─ llm_service.py (NL → DSL conversion via Regex)
  ├─ recursive_compiler.py (DSL → SQL)
  ├─ quarterly_compiler.py (Quarterly financial logic)
  ├─ rule_compiler.py (Alert rule compilation)
  └─ scheduler.py (Background alert checker)

Data Layer:
  ├─ PostgreSQL (Primary database)
  └─ Redis (Query caching)

Utilities:
  ├─ compliance.py (Disclaimers & validation)
  ├─ fetch_yfinance.py (Yahoo Finance data sync)
  ├─ fetch_stock_data.py (AlphaVantage data sync)
  └─ setup_*.py (Database initialization scripts)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+ (optional, for caching)
- API Keys: AlphaVantage (free tier available)

### Installation

1. **Clone and Install Dependencies**
```bash
cd c:\Users\ADMIN\Desktop\Screener
pip install -r requirements.txt
```

2. **Setup Database**
```bash
python setup_database.py          # Create tables
python fetch_yfinance.py          # Populate stock data (130+ symbols)
python setup_portfolio.py         # Add mock holdings
python setup_analyst_data.py      # Add analyst targets
python setup_alerts.py            # Create sample alerts
```

3. **Start Backend**
```bash
uvicorn main:app --reload --port 8000
```

4. **Start Frontend**
```bash
streamlit run streamlit_app.py --server.port 8501
```

5. **Access the App**
- Web UI: http://localhost:8501
- API Docs: http://localhost:8000/docs

## 📊 Database Schema

### Core Tables
- **users** - User accounts with hashed passwords
- **stocks** - Company info (ticker, sector, name)
- **fundamentals** - Valuation metrics (PE, PEG, dividend yield)
- **analysis_target** - Analyst forecasts & price targets
- **quarterly_financials** - Historical earnings data
- **portfolio** - User positions & holdings
- **alerts** - User-defined monitoring rules
- **alert_events** - Triggered alert history
- **query_history** - User searches for analytics

## 🔍 Query Examples

```
"Technology stocks"
"PE < 20 and PEG < 1.5"
"Finance sector with high dividend"
"Revenue growing in last 2 quarters"
"Undervalued Healthcare stocks"
```

## 🔄 Data Flow

1. **User Query** → "Show tech stocks with PE < 25"
2. **NL to DSL** → Regex parsing converts to structured format
3. **DSL to SQL** → Compiles to `SELECT * WHERE sector='Technology' AND pe_ratio < 25`
4. **Database Query** → PostgreSQL executes with parameters
5. **Enrichment** → Add analyst ratings, upside percentages
6. **Caching** → Store results in Redis (5 min TTL)
7. **Response** → JSON with stock list + market insights

## 🔐 Authentication

```python
# Login Flow
POST /login
  ├─ Verify email & password (bcrypt)
  ├─ Generate JWT token
  └─ Return access_token (30 min expiry)

# Protected Endpoints
GET /portfolio
  ├─ Header: Authorization: Bearer <token>
  ├─ Decode JWT
  └─ Fetch user's portfolio
```

## 🚨 Alert System

```
1. User creates alert: "Alert if AAPL price > $150"
2. Scheduler checks every 60 seconds
3. Compares current price vs threshold
4. On match:
   - Insert into alert_events table
   - Send toast notification to frontend
   - Mark as "triggered" (prevent re-firing)
5. User sees notification in Alerts tab
```

## 📁 File Directory

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application & all endpoints |
| `llm_service.py` | Natural language parsing (Regex-based) |
| `recursive_compiler.py` | DSL → SQL compilation |
| `streamlit_app.py` | Frontend UI (Streamlit) |
| `scheduler.py` | Background alert checker |
| `compliance.py` | Disclaimers & compliance checks |
| `fetch_yfinance.py` | Sync stock data from Yahoo Finance |
| `setup_database.py` | Create PostgreSQL schema |
| `dsl_to_sql.py` | DSL conversion utilities |
| `dsl_validator.py` | Validate DSL structures |
| `schemas.py` | Pydantic models for API requests |
| `database.py` | Database connection helpers |
| `hash_password.py` | Password hashing utility |

## 🧪 Testing

Run the included test suites:

```bash
# DSL Compiler Tests
pytest tests/test_compiler.py -v

# Screener API Tests
pytest tests/test_screener.py -v

# Portfolio Logic Tests
pytest tests/test_portfolio.py -v

# Alert System Tests
pytest tests/test_alerts.py -v

# NL Validation Tests
pytest tests/test_validation.py -v

# Manual Integration Tests
python test_nl_queries.py
```

## ⚠️ Important Notes

### Educational Use Only
- This is a **prototype for learning purposes**
- Do NOT use real money until thoroughly validated
- Analyst ratings are subjective; never invest solely on them
- All data is historical/mock for demo purposes

### Compliance Disclaimers
- Platform displays mandatory disclaimers on all screens
- Blocks advisory-like queries: "buy now", "guarantee", "sure shot"
- Returns safe error messages (no internal stack traces)
- All features logged for auditability

### Known Limitations
- NL parsing uses Regex (not ML models) for offline operation
- Alert checking runs every 60 seconds (not real-time)
- Caching may show stale data (5 min TTL)
- AlphaVantage free tier has rate limits (5 calls/min)

## 🔧 Configuration

Edit these files to customize:

```python
# database.py
DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

# main.py
ACCESS_TOKEN_EXPIRE_MINUTES = 30
CACHE_TTL = 300  # 5 minutes
```

## 📈 API Endpoints Summary

### Authentication
- `POST /signup` - Register new user
- `POST /login` - Get JWT token

### Screener
- `POST /screen` - Run NL query (with results)
- `POST /explain-results` - Generate AI analysis

### Portfolio
- `GET /portfolio` - View holdings & P/L

### Alerts
- `POST /alerts` - Create monitoring rule
- `GET /alerts` - List active rules
- `GET /notifications` - Recent triggered alerts

### System
- `GET /health` - Health check (Redis status)

## 🛠️ Troubleshooting

```
❌ "Database Connection Failed"
→ Check PostgreSQL is running on localhost:5434

❌ "Redis Connection Failed (Running in Safe Mode)"
→ Either start Redis or ignore (caching will be disabled)

❌ "No data found for AAPL"
→ Run fetch_yfinance.py first to populate stocks

❌ "Login Invalid"
→ Make sure you've run setup_database.py and signed up
```

## 📚 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit + CSS |
| Backend | FastAPI + Uvicorn |
| Database | PostgreSQL 12+ |
| Caching | Redis 6+ |
| Auth | JWT + bcrypt |
| Data Sync | yfinance, AlphaVantage API |
| Task Scheduler | APScheduler |

## 📝 License

This project is provided as-is for educational purposes.

---

**Made with ❤️ for learning stock screening concepts**
