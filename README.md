# 📈 AI Powered Stock Screener

AI Powered Stock Screener is a full-stack financial analytics platform designed to simplify stock analysis through structured natural-language queries.  
Instead of manually applying filters, users can describe financial conditions in readable text which are internally converted into a Domain Specific Language (DSL), validated, compiled into SQL logic, and executed against a structured financial dataset.

The system combines a FastAPI backend, modular DSL screening engine, alert monitoring workflow, and a Streamlit dashboard interface to demonstrate scalable financial software architecture.

This introduction explains the objective of the system and provides context for the architecture and modules described in the sections below.

---

## 🎯 Project Overview

Traditional stock screeners require complex configuration of filters and technical understanding of financial metrics.  
AI Powered Stock Screener introduces a simple english query-driven workflow where users describe conditions such as:

```text
net profit above 50000 last 4 quarters
```

The application evaluates this request through multiple backend stages:

1. Query parsing and normalization  
2. DSL generation  
3. Validation of supported financial fields  
4. SQL condition building  
5. Database execution  
6. Structured result rendering in the dashboard  

This section explains how the system converts user-friendly queries into controlled backend operations.

---

## ✨ Key Features

### 🔎 Natural-Language Stock Screening
- Query-based filtering instead of manual dropdowns  
- DSL conversion for safe execution  
- Multi-condition logical evaluation  

### 💼 Portfolio Management
- Dynamic portfolio creation  
- Adding holdings directly from screener results  
- Simulated performance monitoring  

### 🔔 Alerts Monitoring System
- DSL-based alert definitions  
- Automated evaluation of stored conditions  
- Trigger history tracking  

### 📊 Financial Data Simulation
- Synthetic time-series updates  
- Quarterly performance comparisons  
- Portfolio recalculation based on simulated prices  

### ⚙️ Modular Backend Engineering
- Independent parser module  
- Validation engine  
- Screener execution layer  
- Alert evaluation system  

This section highlights the primary functional capabilities implemented in the project.

---

## 🧰 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | FastAPI | REST API routing and logic |
| Frontend | Streamlit | Interactive dashboard interface |
| Database | SQLite | Financial dataset storage |
| Programming Language | Python | Core development |
| Data Processing | Pandas | Query result handling |

The technology stack summarizes the tools used to build each system layer.

---

## 🏗️ System Architecture

```text
┌──────────────────────────────────────────────┐
│               Streamlit Frontend              │
│ Screener Interface • Portfolio View • Alerts │
└──────────────────────┬───────────────────────┘
                       │ HTTP Requests
┌──────────────────────▼───────────────────────┐
│               FastAPI Backend                │
│ Authentication • Screener • Portfolio APIs   │
└───────────────┬──────────────────────────────┘
                │
┌───────────────▼──────────────────────────────┐
│ Parser → DSL Builder → Validator → SQL Layer │
└───────────────┬──────────────────────────────┘
                │ SQL Queries
┌───────────────▼──────────────────────────────┐
│                SQLite Database               │
└──────────────────────────────────────────────┘
```

This architecture diagram shows how frontend requests flow through backend processing layers before interacting with the database.

---

## 🔄 Query Evaluation Flow

```text
User Input
   ↓
Parser Module
   ↓
DSL Generation
   ↓
Validation Engine
   ↓
SQL Query Builder
   ↓
Database Execution
   ↓
Dashboard Response
```

Example transformation:

```text
Input Query:
pe < 25 and profit > 5000

Generated SQL:
WHERE pe_ratio < 25 AND profit > 5000
```

This section explains the internal processing pipeline used to execute screening queries.

---
## 🔄 System Workflow

The workflow describes how a user request travels through different layers of the AI Powered Stock Screener system.  
Each stage ensures that queries remain structured, validated, and safely executed.

```text
User enters query in Streamlit UI
        ↓
Frontend sends HTTP request to FastAPI backend
        ↓
Parser module converts natural language into DSL conditions
        ↓
Validator checks supported fields and logical operators
        ↓
Screener engine compiles DSL into SQL query
        ↓
Database executes filtering on financial dataset
        ↓
Results returned to backend API
        ↓
Streamlit dashboard displays structured output
```

### Workflow Explanation

1. **User Interaction**  
   The process begins when the user submits a screening query or portfolio action from the Streamlit dashboard.

2. **API Processing**  
   FastAPI receives the request and forwards the query to backend modules responsible for parsing and execution.

3. **DSL Conversion**  
   The parser transforms readable text into a structured DSL format that the system understands internally.

4. **Validation Layer**  
   The validator ensures only supported financial metrics and safe operations are allowed before database execution.

5. **Query Compilation**  
   The screener module builds SQL conditions based on DSL rules and sends them to the database.

6. **Database Execution**  
   SQLite processes the query and returns matching stock records.

7. **Response Rendering**  
   The backend formats the response and the Streamlit UI displays the results to the user.

This workflow ensures separation of concerns between UI, API logic, DSL processing, and data storage.

## 📂 Project Structure

```bash
stockScreener_project/
│
├── backend/
│   ├── main.py                # FastAPI entry point and API routes
│   ├── parser.py              # Converts natural language into DSL
│   ├── screener.py            # DSL to SQL compiler and execution logic
│   ├── alerts.py              # Alert evaluation and trigger logic
│   ├── validator.py           # DSL validation rules
│   ├── database.py            # Database schema and simulation engine
│   ├── quarterly_compiler.py  # Multi-quarter financial filtering logic
│   └── check_schema.py        # Database inspection utilities
│
├── data/
│   └── stocks.db              # SQLite financial dataset
│
└── frontend/
    └── app.py                 # Streamlit dashboard UI
```

This structure outlines how backend logic, data storage, and frontend components are organized within the repository.

---

## 🗄️ Database Schema

| Table | Fields | Description |
|---|---|---|
| masterstocks | stock_id, symbol, sector | Stock metadata |
| fundamentals | pe_ratio, market_cap, profit | Financial valuation metrics |
| time_series_financials | date, close_price, net_profit | Historical and simulated data |
| portfolio | id, user_id, created_at | Portfolio container |
| portfolio_holdings | portfolio_id, stock_id, quantity, buy_price | Holdings information |
| alerts | id, user_id, query | Stored DSL alert rules |
| alert_triggers | alert_id, triggered_at | Alert evaluation history |

### Relationships

- masterstocks → fundamentals via `stock_id`  
- masterstocks → time_series_financials via `stock_id`  
- portfolio → portfolio_holdings via `portfolio_id`  
- alerts → alert_triggers via `alert_id`

This section documents how financial data and user portfolios are structured within the database.

---

## 📡 API Documentation

### 🔐 Register User

```http
POST /register
Content-Type: application/json
```

```json
{
  "username": "Durga",
  "password": "2005"
}
```

```json
{
  "message": "registered"
}
```

This endpoint creates a new user account in the system.

---

### 🔑 Login

```http
POST /login
```

```json
{
  "token": "generated_token_here"
}
```

This endpoint generates an authentication token required for protected API routes.

---

### 🔎 Screen Stocks

```http
POST /screen
Headers: token: {user_token}
```

```json
{
  "query": "net profit above 50000 last 4 quarters"
}
```

This endpoint executes DSL-based stock screening queries against the financial dataset.

---

### 📁 Create Portfolio

```http
POST /portfolio/create
Headers: token: {user_token}
```

```json
{
  "portfolio_id": 79
}
```

Creates a new portfolio container for managing holdings.

---

### 💼 Add Stock to Portfolio

```http
POST /portfolio/add
Headers: token: {user_token}
```

```json
{
  "portfolio_id": 79,
  "stock_id": 19,
  "quantity": 10,
  "buy_price": 52406
}
```

```json
{
  "message": "added"
}
```

Adds a selected stock into the user’s portfolio.

---

## ⚙️ Setup & Installation Guide

```bash
git clone <repo_url>
cd stockScreener_project
pip install fastapi uvicorn streamlit pandas
cd backend
python database.py
uvicorn main:app --reload
cd frontend
streamlit run app.py
```

This section explains how to run the backend API server and Streamlit dashboard locally.

---

## 🛠️ Troubleshooting

```bash
uvicorn main:app --port 8001
```

```bash
python backend/database.py
```

Common issues include port conflicts, missing database initialization, or expired authentication tokens.

---

## 🚀 Future Improvements

- Integration with real market data APIs for live financial updates  
- Automated background alert scheduler  
- Advanced portfolio analytics and risk visualization  
- Enhanced NLP layer for conversational queries  
- Migration from SQLite to PostgreSQL for production scalability  

This roadmap outlines planned enhancements to extend the platform’s capabilities.

---

## ⚖️ Legal Disclaimer

This application is developed to demonstrate software engineering concepts related to financial data processing and stock screening systems.  
All datasets are used for technical experimentation and architecture demonstration purposes.  
The platform does not provide investment advice, trading recommendations, or financial guarantees.  
Users should independently verify financial decisions before acting on any analysis produced by the system.
