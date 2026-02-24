# StockSense AI - IT Stock Screener

## Project Documentation

A full-stack IT stock screening application with natural language search capabilities, multi-portfolio management, and real-time analytics.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Installation Guide](#installation-guide)
5. [Database Setup](#database-setup)
6. [Running the Application](#running-the-application)
7. [API Endpoints](#api-endpoints)
8. [NLP Search Capabilities](#nlp-search-capabilities)
9. [Project Structure](#project-structure)
10. [Database Schema](#database-schema)

---

## Project Overview

StockSense AI is an intelligent stock screening platform focused on the IT sector. It features 500 IT stocks across 12 sub-sectors with comprehensive financial data. Users can search stocks using natural language queries, manage multiple portfolios, and track their investments with real-time analytics.

### Key Highlights
- **500 IT Stocks** across 12 sub-sectors
- **Natural Language Search** - Query stocks using plain English
- **Multi-Portfolio Management** - Create and manage multiple portfolios
- **Real-time Analytics Dashboard** - Visualize portfolio performance
- **User Authentication** - Secure login and registration system

---

## Features

### 1. Natural Language Stock Search
Search for stocks using queries like:
- "IT stocks with PEG ratio below 3"
- "Cybersecurity stocks likely to beat earnings"
- "Cloud computing stocks with revenue growth above 20%"

### 2. Advanced Filtering Criteria
- **PEG Ratio** - Price/Earnings to Growth ratio
- **Debt to Free Cash Flow** - Financial health indicator
- **Analyst Price Targets** - Compare current price vs analyst targets
- **Revenue Growth YoY** - Year-over-year revenue growth
- **EBITDA Growth YoY** - Profitability growth
- **Earnings Beat Likelihood** - Historical beat rate analysis
- **Upcoming Earnings** - Stocks with earnings within 30 days
- **Share Buybacks** - Companies with active buyback programs

### 3. IT Sub-Sectors Covered
| Sub-Sector | Description |
|------------|-------------|
| Semiconductor | Chip manufacturers and designers |
| Enterprise Software | B2B software solutions |
| Cloud Computing | Cloud infrastructure and services |
| Computer Hardware | PC, server, and device manufacturers |
| Telecom Equipment | Network infrastructure providers |
| Cybersecurity | Security software and services |
| Data Center | Data center REITs and operators |
| AI & Machine Learning | AI-focused companies |
| Fintech | Financial technology |
| Networking | Network equipment and services |
| Gaming | Video game publishers and platforms |
| Internet Services | Online platforms and e-commerce |

### 4. Portfolio Management
- **Multiple Portfolios** - Create separate portfolios for different strategies
- **Holdings Tracking** - Track quantity, average cost, and current value
- **Performance Analytics** - View total value, gains/losses, allocation
- **Weighted Average Cost** - Automatic cost averaging for repeat purchases

### 5. Alert System
- Set price alerts for stocks
- Get notified when stocks hit target prices

---

## Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance Python web framework |
| **Uvicorn** | ASGI server for FastAPI |
| **PostgreSQL** | Relational database |
| **psycopg2** | PostgreSQL adapter for Python |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Streamlit** | Python-based web UI framework |
| **Plotly** | Interactive charting library |
| **Pandas** | Data manipulation |

### NLP Engine
| Component | Purpose |
|-----------|---------|
| **Rule-based Parser** | Pattern matching for query parsing |
| **Regex Patterns** | 20+ patterns for filter extraction |
| **Query Compiler** | Converts parsed filters to SQL |

---

## Installation Guide

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/springboardmentor1077k-prog/Stock-Screener.git
cd Stock-Screener
git checkout Mohammad-Gheta
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
```
fastapi>=0.104.0
uvicorn>=0.24.0
psycopg2-binary>=2.9.9
pydantic>=2.5.0
python-multipart>=0.0.6
streamlit>=1.28.0
requests>=2.31.0
pandas>=2.1.0
plotly>=5.18.0
bcrypt>=4.1.0
python-jose>=3.3.0
passlib>=1.7.4
```

---

## Database Setup

### Step 1: Create Database
```sql
CREATE DATABASE stock_db;
```

### Step 2: Run Schema
```bash
psql -U postgres -d stock_db -f database/schema.sql
```

### Step 3: Seed Data
```bash
python database/data_ingestor.py
```

This will populate the database with 500 IT stocks including:
- 128 real IT companies
- 372 generated stocks with realistic data
- Distribution across all 12 sub-sectors

### Database Configuration
Update credentials in `database/connection.py`:
```python
DB_CONFIG = {
    "host": "localhost",
    "database": "stock_db",
    "user": "postgres",
    "password": "your_password"
}
```

---

## Running the Application

### Step 1: Start the Backend API
```bash
uvicorn backend.api.main:app --reload --port 8000
```
API will be available at: `http://localhost:8000`

### Step 2: Start the Frontend
```bash
streamlit run frontend/streamlit_app/analytics_dashboard.py --server.port 8501
```
Dashboard will be available at: `http://localhost:8501`

### Verify Installation
```bash
# Test API endpoints
curl http://localhost:8000/
curl http://localhost:8000/api/v1/stocks/?limit=5
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | User login |
| GET | `/api/v1/auth/me` | Get current user |

### Stocks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stocks/` | List all stocks (paginated) |
| GET | `/api/v1/stocks/{id}` | Get stock by ID |
| GET | `/api/v1/stocks/search` | NLP search |
| GET | `/api/v1/stocks/sector/{sector}` | Filter by sector |

#### Search Query Parameters
```
GET /api/v1/stocks/search?query=IT stocks with PEG below 2 and revenue growth above 15
```

### Portfolio
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/portfolio/profiles` | List all portfolios |
| GET | `/api/v1/portfolio/holdings` | Get holdings |
| POST | `/api/v1/portfolio/holdings` | Add holding |
| PUT | `/api/v1/portfolio/holdings/{id}` | Update holding |
| DELETE | `/api/v1/portfolio/holdings/{id}` | Delete holding |
| GET | `/api/v1/portfolio/summary` | Portfolio summary |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/alerts/` | List alerts |
| POST | `/api/v1/alerts/` | Create alert |
| DELETE | `/api/v1/alerts/{id}` | Delete alert |

---

## NLP Search Capabilities

The application supports natural language queries that are parsed into database filters.

### Supported Query Patterns

#### Financial Metrics
| Query Example | Filter Applied |
|---------------|----------------|
| "PE below 15" | `pe_ratio < 15` |
| "PEG ratio under 2" | `peg_ratio < 2` |
| "ROE above 20" | `roe > 20` |
| "Debt to equity less than 1" | `debt_to_equity < 1` |

#### Growth Metrics
| Query Example | Filter Applied |
|---------------|----------------|
| "Revenue growth above 25%" | `revenue_growth_yoy > 25` |
| "EBITDA growth over 30%" | `ebitda_growth_yoy > 30` |
| "Earnings growth above 20" | `earnings_growth_rate > 20` |

#### Analyst & Earnings
| Query Example | Filter Applied |
|---------------|----------------|
| "Price below analyst target" | `price_vs_target <= 0` |
| "Near analyst target" | `-10 <= price_vs_target <= 10` |
| "Likely to beat earnings" | `likely_to_beat = true` |
| "Earnings within 30 days" | `earnings_within_30_days = true` |

#### Other Criteria
| Query Example | Filter Applied |
|---------------|----------------|
| "Active buyback" | `buyback_active = true` |
| "Debt to FCF below 4" | `debt_to_fcf < 4` |
| "High promoter holding" | `promoter_holding > 50` |

#### Sub-Sector Filtering
| Query Example | Filter Applied |
|---------------|----------------|
| "Cybersecurity stocks" | `sub_sector = 'Cybersecurity'` |
| "AI ML companies" | `sub_sector = 'AI & Machine Learning'` |
| "Cloud computing" | `sub_sector = 'Cloud Computing'` |

### Complex Query Example
```
"IT stocks with PEG below 3, debt to FCF under 4, revenue growth above 15%, 
likely to beat earnings, and active buyback program"
```

This parses to:
```sql
WHERE sector = 'Technology'
  AND peg_ratio < 3
  AND debt_to_fcf < 4
  AND revenue_growth_yoy > 15
  AND likely_to_beat = true
  AND buyback_active = true
```

---

## Project Structure

```
stock/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── auth.py          # Authentication routes
│   │   ├── stocks.py        # Stock search routes
│   │   ├── portfolio.py     # Portfolio management routes
│   │   └── alerts.py        # Alert system routes
│   └── logic/
│       ├── __init__.py
│       ├── llm_parser.py    # NLP query parser
│       ├── compiler.py      # SQL query compiler
│       ├── engine.py        # Search execution engine
│       └── validator.py     # Input validation
├── database/
│   ├── connection.py        # Database connection pool
│   ├── schema.sql           # Database schema
│   └── data_ingestor.py     # Data seeding script
├── frontend/
│   └── streamlit_app/
│       └── analytics_dashboard.py  # Main Streamlit UI
├── requirements.txt
├── README.md
└── DOCUMENTATION.md
```

---

## Database Schema

### Stocks Table (37 columns)

#### Basic Information
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| symbol | VARCHAR(20) | Stock ticker symbol |
| name | VARCHAR(100) | Company name |
| sector | VARCHAR(50) | Sector (Technology) |
| sub_sector | VARCHAR(50) | IT sub-sector |
| exchange | VARCHAR(10) | Exchange (NSE/BSE/NASDAQ) |

#### Price & Market Data
| Column | Type | Description |
|--------|------|-------------|
| current_price | DECIMAL(12,2) | Current stock price |
| market_cap | DECIMAL(20,2) | Market capitalization |
| volume | BIGINT | Trading volume |

#### Valuation Metrics
| Column | Type | Description |
|--------|------|-------------|
| pe_ratio | DECIMAL(10,2) | Price to Earnings ratio |
| peg_ratio | DECIMAL(10,2) | Price/Earnings to Growth |
| pb_ratio | DECIMAL(10,2) | Price to Book ratio |
| eps | DECIMAL(10,2) | Earnings Per Share |

#### Financial Health
| Column | Type | Description |
|--------|------|-------------|
| debt_to_equity | DECIMAL(10,2) | Debt to Equity ratio |
| roe | DECIMAL(10,2) | Return on Equity |
| free_cash_flow | DECIMAL(20,2) | Free Cash Flow |
| total_debt | DECIMAL(20,2) | Total Debt |
| debt_to_fcf | DECIMAL(10,2) | Debt to FCF ratio |

#### Growth Metrics
| Column | Type | Description |
|--------|------|-------------|
| revenue_growth_yoy | DECIMAL(10,2) | Revenue growth YoY % |
| ebitda | DECIMAL(20,2) | EBITDA value |
| ebitda_growth_yoy | DECIMAL(10,2) | EBITDA growth YoY % |
| earnings_growth_rate | DECIMAL(10,2) | Earnings growth rate |

#### Quarterly Earnings
| Column | Type | Description |
|--------|------|-------------|
| q1_earnings | DECIMAL(20,2) | Q1 earnings |
| q2_earnings | DECIMAL(20,2) | Q2 earnings |
| q3_earnings | DECIMAL(20,2) | Q3 earnings |
| q4_earnings | DECIMAL(20,2) | Q4 earnings |

#### Analyst Data
| Column | Type | Description |
|--------|------|-------------|
| analyst_price_low | DECIMAL(12,2) | Analyst low target |
| analyst_price_high | DECIMAL(12,2) | Analyst high target |
| analyst_price_avg | DECIMAL(12,2) | Analyst average target |
| price_vs_target | DECIMAL(10,2) | % diff from avg target |

#### Earnings Prediction
| Column | Type | Description |
|--------|------|-------------|
| estimated_eps | DECIMAL(10,2) | Estimated EPS |
| historical_beat_rate | DECIMAL(5,2) | Historical beat % |
| likely_to_beat | BOOLEAN | Likely to beat estimate |
| next_earnings_date | DATE | Next earnings date |
| earnings_within_30_days | BOOLEAN | Earnings soon flag |

#### Other
| Column | Type | Description |
|--------|------|-------------|
| promoter_holding | DECIMAL(5,2) | Promoter holding % |
| dividend_yield | DECIMAL(5,2) | Dividend yield % |
| buyback_active | BOOLEAN | Active buyback program |

---

## Screenshots

### Dashboard Home
The main dashboard displays portfolio summary, market overview, and quick search.

### Stock Search
Natural language search interface with filters and results grid.

### Portfolio Management
Multi-portfolio view with holdings, performance charts, and allocation breakdown.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## License

This project is developed for educational purposes as part of the Springboard program.

---

## Author

**Mohammad Gheta**

- GitHub: [springboardmentor1077k-prog/Stock-Screener](https://github.com/springboardmentor1077k-prog/Stock-Screener)
- Branch: Mohammad-Gheta

---

*Last Updated: February 2026*
