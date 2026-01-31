
# Stock Screener Application

A production-grade Stock Screener built with FastAPI, Streamlit, and PostgreSQL.

## Features

- **Authentication**: JWT-based login/signup.
- **Stock Screener**: Filter stocks using a JSON DSL (or natural language).
- **Portfolio Management**: Add/Remove stocks to your personal portfolio.

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Database**: PostgreSQL (via SQLAlchemy)

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**
   Ensure you have a PostgreSQL database running.
   Update `backend/app/core/config.py` with your database URI or set `SQLALCHEMY_DATABASE_URI` environment variable.
   Default: `postgresql://postgres:postgres@localhost:5432/stockscreener`

3. **Run Backend**
   ```bash
   uvicorn backend.app.main:app --reload
   ```
   Explore Swagger UI at http://localhost:8000/api/v1/docs

4. **Run Frontend**
   ```bash
   streamlit run frontend/app.py
   ```
   Open http://localhost:8501

## API Usage Example

**Login:**
POST `/api/v1/auth/login`

**Screen Stocks:**
POST `/api/v1/screener/search`
Header: `Authorization: Bearer <token>`
Body:
```json
{
  "conditions": [
    {"field": "pe_ratio", "operator": "<", "value": 20},
    {"field": "roe", "operator": ">", "value": 15}
  ]
}
```
