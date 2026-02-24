# StockSense AI - Intelligent Stock Screener

An AI-powered stock screening application for Information Technology sector stocks with natural language search capabilities.

## Features

### 🔍 Natural Language Search
Search stocks using plain English queries like:
- "Semiconductor stocks with PEG below 2"
- "IT stocks with buyback and earnings in 30 days"
- "Cloud computing stocks likely to beat earnings"
- "Stocks with PEG < 3, debt repayable in 4 years, revenue growing"

### 📊 500+ IT Sector Stocks
Comprehensive database covering 12 sub-sectors:
- Semiconductor
- Enterprise Software
- Cloud Computing
- Computer Hardware
- Telecom Equipment
- Cybersecurity
- Data Center & Infrastructure
- AI & Machine Learning
- Fintech & Payments
- Networking & Communications
- Gaming & Interactive
- Internet Services

### 📈 Advanced Screening Criteria
- **PEG Ratio** - Price-to-Earnings-Growth ratio
- **Debt to FCF** - How quickly company can repay debt
- **Price vs Analyst Targets** - Below low, near low, mid range, etc.
- **Revenue & EBITDA Growth** - Year-over-year growth rates
- **Earnings Beat Probability** - Based on historical performance
- **Buyback Status** - Companies with announced buybacks
- **Earnings Calendar** - Upcoming earnings within 30 days

### 💼 Multi-Portfolio Management
- Create and manage multiple portfolio profiles
- Track investments across different strategies
- Real-time P/L calculations
- Allocation visualizations

### 🔔 Price Alerts
- Set custom alerts on any stock metric
- Track triggered alerts

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **Database**: PostgreSQL
- **Search**: Rule-based NLP parser

## Project Structure

```
├── backend/
│   ├── api/
│   │   ├── main.py          # FastAPI app entry
│   │   ├── stocks.py        # Stock endpoints
│   │   ├── portfolio.py     # Portfolio endpoints
│   │   ├── alerts.py        # Alert endpoints
│   │   └── auth.py          # Authentication
│   └── logic/
│       ├── llm_parser.py    # NLP query parser
│       ├── compiler.py      # SQL query compiler
│       ├── validator.py     # Query validation
│       └── engine.py        # Search engine
├── database/
│   ├── connection.py        # DB connection
│   ├── data_ingestor.py     # 500 stock data generator
│   └── schema.sql           # Database schema
├── frontend/
│   └── streamlit_app/
│       └── analytics_dashboard.py  # Main UI
└── requirements.txt
```

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/springboardmentor1077k-prog/Stock-Screener.git
cd Stock-Screener
git checkout Mohammad-Gheta
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup PostgreSQL Database**
```bash
# Create database
psql -U postgres -c "CREATE DATABASE stock_db;"

# Run schema
psql -U postgres -d stock_db -f database/schema.sql
```

5. **Configure database connection**
Update `database/connection.py` with your PostgreSQL credentials.

6. **Seed the database**
```bash
python -m database.data_ingestor
```

7. **Run the application**

Start FastAPI backend:
```bash
uvicorn backend.api.main:app --reload
```

Start Streamlit frontend (in new terminal):
```bash
streamlit run frontend/streamlit_app/analytics_dashboard.py --server.port 8501
```

8. **Access the application**
- Frontend: http://localhost:8501
- API Docs: http://localhost:8000/docs

## Sample Queries

```
"Show me semiconductor stocks with PEG ratio less than 2"
"IT stocks with buyback announced and earnings within 30 days"
"Cloud computing stocks likely to beat earnings estimates"
"Stocks with debt repayable in 4 years, revenue and ebitda growing"
"Cybersecurity stocks with price below analyst targets"
"AI stocks with positive revenue growth"
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stocks/` | GET | List all stocks |
| `/api/v1/stocks/search?query=` | GET | NLP-powered search |
| `/api/v1/stocks/{symbol}` | GET | Stock details |
| `/api/v1/portfolio/profiles` | GET | List portfolios |
| `/api/v1/portfolio/holdings` | GET | Portfolio holdings |
| `/api/v1/portfolio/add` | POST | Add holding |
| `/api/v1/alerts/` | GET | List alerts |

## Author

Mohammad Gheta

## Disclaimer

This application is for educational and informational purposes only. It does not constitute financial advice. Always consult with a qualified financial advisor before making investment decisions.
