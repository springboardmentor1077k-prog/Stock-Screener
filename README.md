```markdown
# 📈 AI Stock Screener

An intelligent, full-stack stock screening and portfolio management dashboard built with FastAPI and Streamlit. 

Instead of manually filtering through spreadsheets, this application allows users to query the stock market using natural language (e.g., *"Show me IT stocks with a PE ratio under 30"*). It also features simulated portfolio tracking, live price alerts, and in-depth financial charting.

## ✨ Features
* **🤖 AI-Powered Screener:** Use natural language to filter and discover stocks instantly.
* **⚡ Blazing Fast Performance:** Redis caching ensures near-instant page loads and API responses.
* **💼 Portfolio Management:** Track your holdings, simulate buys/sells, and monitor your live P&L.
* **🔔 Smart Price Alerts:** Set custom target prices and condition thresholds.
* **📊 Interactive Charts:** Deep dive into stock fundamentals and historical quarterly financial trends.
* **🔒 Secure Authentication:** JWT-based login system with securely hashed passwords.

## 🛠️ Tech Stack
* **Frontend:** Streamlit, Pandas, Requests
* **Backend:** FastAPI, Python, JWT Authentication
* **Database:** PostgreSQL, SQLAlchemy ORM
* **Caching & Performance:** Redis
* **Data Source:** Yahoo Finance API (`yfinance`)
* **AI Engine:** Custom LLM Query Parser 

## 🚀 Getting Started

### 1. Prerequisites
Make sure you have the following installed on your machine:
* Python 3.8+
* PostgreSQL
* Redis Server (Running on default port `6379`)

### 2. Installation
Clone the repository and navigate into the project directory:
```bash
git clone [https://github.com/yourusername/ai-stock-screener.git](https://github.com/yourusername/ai-stock-screener.git)
cd ai-stock-screener

```

Create and activate a virtual environment:

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

```

Install the required dependencies:

```bash
pip install -r backend/requirements.txt

```

### 3. Database & Environment Setup

1. Create a PostgreSQL database named `stock_screener_db1`.
2. Create a `.env` file in the root directory and add your secret keys:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost/stock_screener_db1
SECRET_KEY=your_super_secret_jwt_key

```

3. Run the initial data ingestion to populate the database:

```bash
python -m backend.seed_data
python -m backend.ingestion

```

### 4. Running the Application

You will need two terminal windows to run the full-stack application.

**Terminal 1: Start the Backend (FastAPI)**

```bash
uvicorn backend.main:app --reload

```

**Terminal 2: Start the Frontend (Streamlit)**

```bash
streamlit run app.py

```

Open your browser and navigate to `http://localhost:8501` to use the application. Log in with your admin credentials to get started!

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

```

***

### **What to do next**
Make sure to replace `https://github.com/yourusername/ai-stock-screener.git` in the installation step with your actual GitHub link! 

Would you like to move on to setting up the **Background Scheduler** now so your database updates live market prices automatically?

If you want to style your documentation further, checking out this [comprehensive Markdown crash course](https://www.youtube.com/watch?v=_PPWWRV6gbA) is a great way to learn advanced formatting tricks that make GitHub repositories stand out.


http://googleusercontent.com/youtube_content/0

```
