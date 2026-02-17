# Stock Analytics Platform - Complete Documentation

![Stock Analytics Platform](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Performance & Caching](#performance--caching)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Project Overview

**Stock Analytics Platform** is a production-grade stock market analysis and portfolio management system. It enables users to:
- Screen stocks using natural language queries
- Manage investment portfolios
- Set up intelligent price alerts
- Analyze market trends and portfolio performance
- Access real-time market data

The system is built with a **FastAPI backend** for robust API handling and a **Streamlit frontend** for interactive user interface, complemented by an **LLM-powered AI engine** for natural language query processing.

### Core Use Cases
1. **Stock Screening**: Find stocks matching specific criteria
2. **Portfolio Tracking**: Monitor holdings and performance
3. **Alert Management**: Get notified when stocks hit target prices
4. **Market Analysis**: View analytics and trends

---

## ✨ Key Features

### 1. **Authentication & Authorization**
- ✅ User registration and login
- ✅ Secure password validation
- ✅ Session management
- ✅ User role support

### 2. **Stock Screener**
- ✅ Natural language query processing ("Show me tech stocks with PE < 20")
- ✅ DSL-to-SQL compilation
- ✅ Advanced filtering (sector, market cap, custom conditions)
- ✅ Machine learning-powered compliance validation
- ✅ Query result caching
- ✅ Sub-500ms response times

### 3. **Portfolio Management**
- ✅ View portfolio holdings
- ✅ Add/remove stocks
- ✅ Real-time P&L calculation
- ✅ Portfolio valuation
- ✅ Multi-portfolio support
- ✅ Performance analytics

### 4. **Alert System**
- ✅ Price-based alerts
- ✅ Condition-based triggers (Above/Below)
- ✅ Real-time trigger detection
- ✅ Alert history tracking
- ✅ Duplicate detection
- ✅ Alert enable/disable toggle

### 5. **Dashboard & Analytics**
- ✅ Portfolio summary cards
- ✅ Interactive charts (Plotly)
- ✅ Sector distribution visualization
- ✅ Performance trends
- ✅ Key metrics display
- ✅ Real-time data updates

### 6. **Enterprise Features**
- ✅ Comprehensive error handling
- ✅ Database retry logic
- ✅ Compliance validation
- ✅ Structured logging
- ✅ CORS support
- ✅ Request validation

---

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                  Frontend Layer                      │
│  (Streamlit Dashboard + Auth UI + Compliance UI)     │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────┐
│              FastAPI Backend (Port 8000)             │
│  ┌─────────────────────────────────────────────┐    │
│  │  API Endpoints (Screen, Portfolio, Alerts)  │    │
│  └────────────┬────────────────────────────────┘    │
│               │                                      │
│  ┌────────────▼──────────────────────────────────┐  │
│  │         Service Layer                         │  │
│  │ ┌──────────────┐ ┌──────────┐ ┌────────────┐ │  │
│  │ │ Screener     │ │Portfolio │ │ Alerts     │ │  │
│  │ │ Service      │ │ Service  │ │Service     │ │  │
│  │ └──────────────┘ └──────────┘ └────────────┘ │  │
│  └────────────┬─────────────────────────────────┘  │
│               │                                      │
│  ┌────────────▼──────────────────────────────────┐  │
│  │      Utility & Support Layers                 │  │
│  │ ┌──────────────────────────────────────────┐ │  │
│  │ │ Cache | DB Retry | Logging | Exceptions │ │  │
│  │ └──────────────────────────────────────────┘ │  │
│  └────────────┬─────────────────────────────────┘  │
└────────────────┼──────────────────────────────────┘
                 │ SQL
┌────────────────▼──────────────────────────────────┐
│          AI/ML Layer (LLM Integration)             │
│  - Natural Language Processing                     │
│  - Query Compilation                               │
│  - Compliance Validation                           │
└────────────┬───────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────┐
│           SQLite Database                          │
│  ┌──────────────────────────────────────────────┐ │
│  │ stocks | portfolios | alerts | holdings | .. │ │
│  └──────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Interactive web UI |
| **Backend** | FastAPI | REST API server |
| **Database** | SQLite | Data storage |
| **AI/ML** | LLM (OpenAI/Custom) | NLP query processing |
| **Caching** | In-memory cache | Performance optimization |
| **Charting** | Plotly | Data visualization |
| **Server** | Uvicorn | ASGI application server |

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum (4GB recommended)
- **Disk Space**: 500MB
- **Internet**: Required for stock data and AI API calls

### Recommended Setup
- **OS**: Windows 11 / macOS 12+ / Linux (Ubuntu 20.04+)
- **Python**: 3.10+
- **RAM**: 8GB+
- **CPU**: Multi-core processor
- **Database**: SSD for better performance

---

## 📦 Installation Guide

### Step 1: Clone the Repository

```bash
cd c:\Users\Lenovo\Desktop\Stock screener app (Project)\Stock-Screener
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install backend dependencies
pip install fastapi uvicorn pandas plotly streamlit

# Install additional required packages
pip install python-dotenv pydantic sqlalchemy requests
```

### Step 4: Configure Environment

Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_PATH=./stock_screener.db
DATABASE_ECHO=False

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# AI/LLM Configuration
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# Cache Configuration
CACHE_TTL=300  # 5 minutes
CACHE_MAX_SIZE=1000

# Compliance
COMPLIANCE_LEVEL=STRICT
```

### Step 5: Initialize Database

```bash
python inspect_database.py
```

This script will:
- Create database tables
- Initialize default data
- Verify database integrity

---

## 🚀 Running the Application

### Option 1: Run with Batch File (Recommended for Windows)

```bash
# Open Command Prompt or PowerShell
cd "c:\Users\Lenovo\Desktop\Stock screener app (Project)\Stock-Screener"
run_all_demos.bat
```

### Option 2: Manual Startup

**Terminal 1 - Start Backend API Server**

```bash
cd "c:\Users\Lenovo\Desktop\Stock screener app (Project)\Stock-Screener\fastapi_backend"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Start Frontend Dashboard**

```bash
cd "c:\Users\Lenovo\Desktop\Stock screener app (Project)\Stock-Screener\Streamlit_Dashboard"
streamlit run app.py
```

### Option 3: Using Docker (Optional)

```bash
# Build Docker image
docker build -t stock-screener .

# Run container
docker run -p 8000:8000 -p 8501:8501 stock-screener
```

### Verification

After startup, verify:
- ✅ API Server: `http://localhost:8000/docs` (Swagger UI)
- ✅ Frontend: `http://localhost:8501` (Streamlit Dashboard)
- ✅ Health Check: `GET http://localhost:8000/health`

---

## 🔌 API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication Endpoints

#### Register User
```http
POST /register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}

Response: 200 OK
{
  "status": "success",
  "user_id": 1,
  "message": "User registered successfully"
}
```

#### Login
```http
POST /login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123!"
}

Response: 200 OK
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 1
}
```

### Screener Endpoints

#### Screen Stocks
```http
POST /screen
Content-Type: application/json

{
  "query": "Show me technology stocks with PE ratio below 20",
  "sector": "Technology",
  "strong_only": true,
  "market_cap_filter": "Large Cap"
}

Response: 200 OK
{
  "results": [
    {
      "symbol": "AAPL",
      "company_name": "Apple Inc.",
      "price": 150.25,
      "pe_ratio": 18.5,
      "market_cap": "$2.8T",
      "sector": "Technology"
    },
    ...
  ],
  "count": 15,
  "cached": false,
  "latency_ms": 245
}
```

### Portfolio Endpoints

#### Get Portfolio
```http
GET /portfolio
Headers: Authorization: Bearer {token}

Response: 200 OK
{
  "portfolio": [
    {
      "symbol": "AAPL",
      "quantity": 10,
      "avg_buy_price": 145.00,
      "current_price": 150.25,
      "profit_loss": 52.50,
      "profit_loss_percent": 3.62
    },
    ...
  ],
  "total_value": 5250.75,
  "total_profit_loss": 125.30
}
```

#### Add Stock to Portfolio
```http
POST /portfolio/add
Content-Type: application/json
Headers: Authorization: Bearer {token}

{
  "symbol": "GOOGL",
  "quantity": 5,
  "buy_price": 140.00
}

Response: 201 Created
{
  "status": "success",
  "message": "Stock added to portfolio",
  "holding": {
    "symbol": "GOOGL",
    "quantity": 5,
    "avg_buy_price": 140.00
  }
}
```

#### Remove Stock from Portfolio
```http
DELETE /portfolio/GOOGL
Headers: Authorization: Bearer {token}

Response: 200 OK
{
  "status": "success",
  "message": "Stock removed from portfolio"
}
```

### Alert Endpoints

#### Create Alert
```http
POST /alerts/create
Content-Type: application/json
Headers: Authorization: Bearer {token}

{
  "symbol": "AAPL",
  "condition": "Above",
  "value": 155.00
}

Response: 201 Created
{
  "status": "success",
  "alert_id": 1,
  "message": "Alert created successfully"
}
```

#### Get Alerts
```http
GET /alerts
Headers: Authorization: Bearer {token}

Response: 200 OK
{
  "alerts": [
    {
      "id": 1,
      "symbol": "AAPL",
      "condition": ">",
      "threshold": 155.00,
      "is_active": true,
      "last_trigger_time": "2026-02-17T10:30:00"
    },
    ...
  ]
}
```

#### Update Alert Status
```http
PUT /alerts/1
Content-Type: application/json
Headers: Authorization: Bearer {token}

{
  "is_active": false
}

Response: 200 OK
{
  "status": "success",
  "message": "Alert updated"
}
```

### Interactive API Documentation
Access the full interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 📊 Database Schema

### Tables Overview

#### `stocks`
```sql
CREATE TABLE stocks (
  symbol TEXT PRIMARY KEY,
  company_name TEXT NOT NULL,
  price FLOAT,
  pe_ratio FLOAT,
  earnings_growth FLOAT,
  market_cap TEXT,
  sector TEXT
);
```

#### `portfolios`
```sql
CREATE TABLE portfolios (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `portfolio_holdings`
```sql
CREATE TABLE portfolio_holdings (
  id INTEGER PRIMARY KEY,
  portfolio_id INTEGER NOT NULL,
  stock_id TEXT NOT NULL,
  quantity INTEGER,
  avg_buy_price FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
  FOREIGN KEY (stock_id) REFERENCES stocks(symbol)
);
```

#### `alerts`
```sql
CREATE TABLE alerts (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  portfolio_id INTEGER NOT NULL,
  metric TEXT NOT NULL,
  operator TEXT NOT NULL,
  threshold FLOAT NOT NULL,
  is_active BOOLEAN DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_trigger_time TIMESTAMP
);
```

#### `alert_events`
```sql
CREATE TABLE alert_events (
  id INTEGER PRIMARY KEY,
  alert_id INTEGER NOT NULL,
  triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  triggered_value FLOAT,
  FOREIGN KEY (alert_id) REFERENCES alerts(id)
);
```

#### `analyst_ratings`
```sql
CREATE TABLE analyst_ratings (
  id INTEGER PRIMARY KEY,
  symbol TEXT NOT NULL,
  rating TEXT,
  target_price FLOAT,
  analyst TEXT,
  FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);
```

---

## 📁 Project Structure

```
Stock-Screener/
│
├── fastapi_backend/              # Backend API Server
│   ├── main.py                   # FastAPI application entry
│   ├── models.py                 # Pydantic request/response models
│   ├── verify_resilience.py      # Resilience testing
│   ├── services/                 # Business logic services
│   │   ├── screener.py           # Stock screening logic
│   │   ├── portfolio.py          # Portfolio management
│   │   ├── alerts.py             # Alert management
│   │   └── cache.py              # Caching layer
│   └── utils/                    # Utility modules
│       ├── database.py           # Database connection
│       ├── logging_config.py     # Logging setup
│       ├── exceptions.py         # Custom exceptions
│       └── retries.py            # Retry logic
│
├── Streamlit_Dashboard/          # Frontend Dashboard
│   ├── app.py                    # Main dashboard app
│   ├── auth_ui.py                # Authentication UI
│   ├── ai_service.py             # AI integration
│   ├── server.py                 # Server config
│   └── utils/                    # Frontend utilities
│       ├── api.py                # API communication
│       ├── auth.py               # Auth helpers
│       └── compliance.py         # Compliance UI
│
├── dsl_engine/                   # DSL Compilation
│   ├── compiler.py               # DSL to SQL compiler
│   ├── validator.py              # Query validator
│   ├── schema.py                 # Schema definitions
│   └── test_dsl.py               # DSL tests
│
├── tables/                       # Database table definitions
│   ├── stocks.py
│   ├── portfolios.py
│   ├── alerts.py
│   └── ...
│
├── demos/                        # Demo scripts
│   ├── demo1_portfolio.py
│   ├── demo2_portfolio_success.py
│   ├── demo3_live_alerts.py
│   └── ...
│
├── test/                         # Test suite
│   ├── testing_alerts.py
│   ├── testing_compiler.py
│   ├── testing_portfolio.py
│   └── testing_screener_execution.py
│
├── requirements.txt              # Project dependencies
├── pytest.ini                    # Pytest configuration
└── README.md                     # This file
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_PATH` | str | `./stock_screener.db` | SQLite database file path |
| `API_HOST` | str | `0.0.0.0` | API server host |
| `API_PORT` | int | `8000` | API server port |
| `OPENAI_API_KEY` | str | - | OpenAI API key for LLM |
| `LOG_LEVEL` | str | `INFO` | Logging level |
| `CACHE_TTL` | int | `300` | Cache time-to-live (seconds) |
| `COMPLIANCE_LEVEL` | str | `STRICT` | Compliance validation level |

### Custom Configuration

Edit `fastapi_backend/utils/logging_config.py`:
```python
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': './logs/app.log'
}
```

---

## 📖 Usage Examples

### Example 1: Stock Screening with Natural Language

```python
# User Input via UI
query = "Show me healthcare stocks with earnings growth above 15%"

# System Process:
# 1. LLM converts to DSL
# 2. DSL compiler generates SQL
# 3. Database executes query
# 4. Results cached and returned

# Expected Output:
# - List of healthcare stocks matching criteria
# - Execution time: ~200-300ms
# - Results cached for future identical queries
```

### Example 2: Portfolio Management

```python
# User adds stock to portfolio
POST /portfolio/add
{
  "symbol": "MSFT",
  "quantity": 10,
  "buy_price": 300.00
}

# System:
# 1. Validates stock exists
# 2. Checks for duplicates
# 3. Inserts into portfolio_holdings
# 4. Calculates initial P&L

# Result:
# Portfolio value updated, profit/loss tracked
```

### Example 3: Setting Up Alerts

```python
# User creates price alert
POST /alerts/create
{
  "symbol": "TSLA",
  "condition": "Below",
  "value": 250.00
}

# System:
# 1. Validates alert doesn't exist
# 2. Creates alert record
# 3. Enables real-time monitoring
# 4. Triggers when condition met

# Notification:
# Email/UI notification when TSLA price drops below $250
```

---

## ⚠️ Error Handling

### Error Response Format

All errors return standardized JSON:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid input provided",
  "details": {
    "field": "pe_ratio",
    "issue": "must be positive number"
  }
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| `200` | OK | Successful request |
| `201` | Created | Resource created |
| `400` | Bad Request | Invalid input |
| `401` | Unauthorized | Missing/invalid auth |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Duplicate alert |
| `422` | Unprocessable Entity | Validation error |
| `500` | Server Error | Database failure |

### Custom Exception Types

```python
# Validation errors
ValidationException: Invalid input data

# Database errors  
DatabaseException: Connection/query failures

# Business logic errors
ComplianceException: Query violates compliance
DuplicateAlertException: Alert already exists

# System errors
SystemException: Unrecoverable failures
```

---

## ⚡ Performance & Caching

### Cache Strategy

- **Screener Results**: 5-minute TTL, LRU eviction
- **Portfolio Data**: 1-minute TTL, real-time updates
- **Stock Prices**: 2-minute TTL, frequent updates

### Performance Benchmarks

| Operation | Target | Achieved |
|-----------|--------|----------|
| Stock Screening | <500ms | 200-400ms |
| Portfolio Fetch | <300ms | 100-200ms |
| Alert Creation | <200ms | 50-150ms |
| Authentication | <400ms | 150-300ms |

### Optimization Tips

1. **Use Caching**: Repeated queries return cached results
2. **Batch Operations**: Create multiple alerts in one request
3. **Lazy Load**: Load data on demand, not upfront
4. **Index Optimization**: Ensure database indexes on frequently queried columns

---

## 🐛 Troubleshooting

### Issue: Port 8000 Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or use different port
uvicorn main:app --port 8001
```

### Issue: Database Locked

```bash
# Ensure only one instance is running
# Check for zombie processes
# SQLite may need timeout adjustment

# In database.py:
connection.execute("PRAGMA busy_timeout = 5000")
```

### Issue: LLM API Key Invalid

```bash
# Verify .env file
# Check API key in OpenAI dashboard
# Ensure key has appropriate permissions
# Test with: curl -H "Authorization: Bearer <key>" https://api.openai.com/v1/models
```

### Issue: Streamlit Not Starting

```bash
# Clear cache
streamlit cache clear

# Check Python version
python --version

# Reinstall streamlit
pip install --upgrade streamlit
```

### Issue: CORS Errors in Frontend

```python
# Verify CORS configuration in main.py
# Should allow all origins for development:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🧪 Testing

### Run All Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run test suite
pytest test/

# With coverage report
pytest test/ --cov=fastapi_backend --cov-report=html
```

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction
3. **E2E Tests**: Full user workflows
4. **Performance Tests**: Load and stress testing
5. **Edge Case Tests**: Boundary conditions

### Test Files

- `test/testing_alerts.py` - Alert system tests
- `test/testing_compiler.py` - DSL compiler tests
- `test/testing_portfolio.py` - Portfolio tests
- `test/testing_screener_execution.py` - Screener tests
- `test/testing_validation.py` - Validation tests

---

## 📝 API Rate Limiting

Default rate limits per hour:
- Authenticated users: 1000 requests
- Unauthenticated users: 100 requests
- AI/LLM calls: 50 requests

Configure in `main.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/screen")
@limiter.limit("50/hour")
async def screen_stocks(request: ScreenRequest):
    ...
```

---

## 🔐 Security Features

### Authentication
- ✅ Secure password hashing
- ✅ JWT token-based auth
- ✅ Session timeout (24 hours)
- ✅ HTTPS support (production)

### Data Protection
- ✅ SQL injection prevention (parameterized queries)
- ✅ Input validation (Pydantic models)
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ Error message sanitization

### Compliance
- ✅ GPL compliance checks
- ✅ Query validation
- ✅ Suspicious activity logging
- ✅ Audit trail for sensitive operations

---

## 📱 UI Features

### Dashboard
- Portfolio summary cards
- Interactive charts (Plotly)
- Real-time metrics
- Dark/light mode toggle

### Stock Screener
- Natural language query input
- Advanced filters
- Results table with sorting/filtering
- Export functionality

### Portfolio Management
- Holdings overview
- Add/remove stocks
- P&L tracking
- Performance analytics

### Alerts
- Create/manage alerts
- Alert history
- Trigger notifications
- Alert statistics

---

## 🚀 Deployment

### Development Deployment

```bash
# Terminal 1: Backend
cd fastapi_backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd Streamlit_Dashboard
streamlit run app.py
```

### Production Deployment

#### Using Gunicorn + Nginx

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 fastapi_backend.main:app

# Nginx configuration
server {
    listen 80;
    server_name yourdomain.com;
    
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

#### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 8501

CMD ["sh", "-c", "uvicorn fastapi_backend.main:app --host 0.0.0.0 --port 8000 & streamlit run Streamlit_Dashboard/app.py --server.port 8501"]
```

### Cloud Deployment (AWS, GCP, Azure)

Deploy using:
- **AWS**: Elastic Beanstalk
- **GCP**: Cloud Run
- **Azure**: App Service
- **Heroku**: Git push deployment

---

## 📞 Support & Contact

### Getting Help

1. **Check README**: Review this documentation
2. **Search Issues**: Check GitHub issues for similar problems
3. **Testing**: Run test suite to verify installation
4. **Logging**: Check `logs/app.log` for detailed error messages

### Community

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Join community discussions
- **Email**: support@stockanalytics.com

---

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repo-url>
cd Stock-Screener

# Create branch
git checkout -b feature/your-feature-name

# Make changes, test, commit
git add .
git commit -m "Add feature description"
git push origin feature/your-feature-name

# Create Pull Request
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings
- Add unit tests for new features
- Keep functions small and focused

### Pull Request Process

1. Update README if needed
2. Add/update tests
3. Ensure all tests pass
4. Request code review
5. Wait for approval and merge

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## ⚖️ Legal Disclaimer

**This application is provided for educational and research purposes only.** It is not financial advice. Users are responsible for:
- Verifying all stock data accuracy
- Complying with securities regulations
- Understanding investment risks
- Consulting financial advisors

---

## 📊 Project Statistics

- **Lines of Code**: 15,000+
- **API Endpoints**: 12+
- **Database Tables**: 6+
- **Test Cases**: 50+
- **Documentation Pages**: 100+

---

## 🔄 Version History

### v1.0.0 (Current)
- ✅ Complete stock screening system
- ✅ Portfolio management
- ✅ Alert system
- ✅ AI/LLM integration
- ✅ Production-ready backend

### Upcoming (v1.1.0)
- Mobile app (Flutter)
- Advanced charting
- Social features
- Email notifications
- Two-factor authentication

---

## 🙏 Acknowledgments

Built with:
- FastAPI - Modern Python web framework
- Streamlit - Rapid UI development
- SQLite - Lightweight database
- Plotly - Interactive visualizations
- OpenAI - LLM capabilities

---

**Last Updated**: February 17, 2026  
**Maintainer**: Stock Analytics Team  
**Status**: Production Ready ✅

For the latest information, visit [GitHub Repository](https://github.com/yourusername/stock-screener)

---

**Happy Screening! 📈**
