# AI Stock Screener (Beta)

An AI-based stock analysis and portfolio management tool built as a student project for the Indian stock market, allowing users to explore data with natural language, manage portfolios, and monitor performance in an easy-to-use interface.
---

## 🚀 Key Features

- **🧠 AI-Powered Market Screening**: Execute complex queries using plain English (e.g., *"Large cap companies with PE < 15 and profitable for last 8 quarters"*).
- **💼 Advanced Portfolio Management**: Track multiple portfolios with granular holding details, real-time gain/loss metrics, and investment summaries.
- **🔔 Proactive Alert System**: (Formerly History) Set and manage price-threshold alerts. Stay informed on market movements with an integrated polling mechanism.
- **📈 Comprehensive Data Pipeline**: Automated ingestion of company profiles, technical fundamentals, and quarterly financial statements.
- **🌑 Premium Visual Experience**: A sleek, dark-themed dashboard optimized for high-density financial data.

---

## 📂 Project Architecture

```text
stock-screener/
├── backend/
│   ├── api/                # Core API Layer (FastAPI, JWT Auth, Main Router)
│   ├── logic/              # Engine Layer (DSL Compiler, Validator, LLM Integration)
│   └── ...                 # Feature-specific services
├── database/               # Data Persistance & Pipeline
│   ├── connection.py       # DB Pool management
│   ├── data_ingestor.py    # Master ingestion conductor
│   └── ...                 # Modular ingestion scripts (Stocks, Fundamentals)
├── frontend/               # User Interface Layer
│   └── analytics_dashboard.py # Streamlit Integrated Dashboard
└── requirements.txt        # Managed Dependencies
```

---

## ⚙️ Setup & Deployment

### 1. Requirements
* **Python**: 3.9 or higher
* **Database**: PostgreSQL 14+
* **LLM Access**: [Groq Cloud API Key](https://console.groq.com/) (Free tier available)
* **Market Data**: Alpha Vantage API Key (Optional fallback)

### 2. Environment Configuration
Initialize a `.env` file in the root directory:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_NAME=stock_screener
JWT_SECRET_KEY=generate_a_secure_random_string
GROQ_API_KEY=gsk_your_key_here
ALPHA_VANTAGE_API_KEY=your_av_key_here
```

### 3. Application Installation
```bash
# Initialize Virtual Environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install Core Dependencies
pip install -r requirements.txt
```

### 4. Database Population
Sync the latest Indian stock data to your local PostgreSQL instance:
```bash
python database/data_ingestor.py
```

---

## 🏃 Running the Platform

To run the full suite, you will need two terminal sessions:

### Session A: Backend API
Runs the FastAPI server at `http://localhost:8001`.
```bash
python -m uvicorn backend.api.main:app --port 8001 --reload
```

### Session B: Frontend UI
Launches the Streamlit browser interface.
```bash
streamlit run frontend/analytics_dashboard.py
```

---

## 🛡️ Disclaimer
*This software is developed for educational and experimental purposes. The authors do not provide financial advice. Always verify data with official SEBI/NSE sources before making investment decisions.*
