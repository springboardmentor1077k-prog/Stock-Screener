# Stock Screener API with JWT Authentication

Complete FastAPI + Streamlit authentication system with protected endpoints.

## 📋 Features

- **JWT Authentication** - Secure token-based authentication
- **Protected Endpoints** - API endpoints requiring valid token
- **Streamlit Frontend** - User-friendly login and data access
- **Token Storage** - Tokens stored in Streamlit session state
- **Database Integration** - Fetch stock data from PostgreSQL

## 🛠️ Installation

### 1. Install dependencies

```bash
pip install fastapi uvicorn pydantic psycopg2-binary passlib bcrypt python-jose pyjwt streamlit requests
```

### 2. Setup Database

Make sure your PostgreSQL database is running with:
- Database: `stock_screener`
- Tables: `stocks`, `fundamentals`
- User: `postgres` / Password: `aarya`

## 🚀 Running the Application

### Terminal 1: Start FastAPI Server

```bash
python app.py
```

The API will run at: `http://127.0.0.1:8000`

API Documentation available at: `http://127.0.0.1:8000/docs`

### Terminal 2: Start Streamlit Frontend

```bash
streamlit run streamlit_app.py
```

The frontend will open at: `http://localhost:8501`

## 🔐 Demo Credentials

| Username | Password    |
|----------|-------------|
| admin    | admin123    |
| user     | user123     |

## 📡 API Endpoints

### 1. Login (Public)
```
POST /login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Get All Stocks (Protected)
```
GET /stocks
Authorization: Bearer <access_token>

Response:
{
  "count": 2,
  "stocks": [
    {
      "stock_id": 320193,
      "company_name": "Apple Inc",
      "sector": "TECHNOLOGY",
      "pe_ratio": 35.22,
      "peg_ratio": 2.655
    }
  ],
  "accessed_by": "admin"
}
```

### 3. Get Stock by ID (Protected)
```
GET /stocks/{stock_id}
Authorization: Bearer <access_token>

Response:
{
  "stock_id": 320193,
  "company_name": "Apple Inc",
  "sector": "TECHNOLOGY",
  "pe_ratio": 35.22,
  "peg_ratio": 2.655,
  "accessed_by": "admin"
}
```

## 🔑 How Authentication Works

1. **Login** → User enters credentials on Streamlit
2. **Get Token** → FastAPI validates and returns JWT token
3. **Store Token** → Streamlit stores in session state
4. **Send Request** → Token included in `Authorization: Bearer <token>` header
5. **Verify Token** → FastAPI validates token on protected endpoints
6. **Access Data** → If valid, user gets data; if invalid, 401 error

## 🛡️ Security Notes

⚠️ **IMPORTANT**: Change `SECRET_KEY` in `app.py` for production!

```python
SECRET_KEY = "your-secret-key-change-this"  # Change this!
```

For production:
- Use strong random SECRET_KEY
- Store credentials in environment variables
- Use HTTPS
- Add rate limiting
- Implement user database instead of demo credentials

## 🧪 Testing with cURL

```bash
# 1. Login
curl -X POST "http://127.0.0.1:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. Use token to access protected endpoint
curl -X GET "http://127.0.0.1:8000/stocks/320193" \
  -H "Authorization: Bearer <your_token_here>"
```

## 📁 File Structure

```
Screener/
├── app.py                 # FastAPI application with JWT auth
├── streamlit_app.py       # Streamlit frontend
├── fetch_stock_data.py    # Stock data fetching script
└── README.md             # This file
```

## ❌ Common Issues

| Issue | Solution |
|-------|----------|
| Connection refused | Make sure FastAPI is running on port 8000 |
| Token expired | Login again to get a new token |
| Database error | Verify PostgreSQL is running and credentials are correct |
| Invalid token | Check that token is correctly passed in header |

## 📚 Learn More

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Tokens](https://jwt.io/)
- [Streamlit Session State](https://docs.streamlit.io/library/api-reference/session-state)
