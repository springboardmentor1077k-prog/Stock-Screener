# 📊 AI StockLens – Intelligent Stock Analysis Platform

AI StockLens is an AI-powered stock analytics and visualization platform developed as part of the Infosys Springboard Internship.  
This project enables users to explore stock market data, analyze financial signals, and interact with insights using an intuitive dashboard and NLP-based query system.

---

## 🚀 Features

- 📈 Interactive stock analysis dashboard  
- 🔎 Market explorer for stock insights  
- 📊 Portfolio and holdings visualization  
- 🤖 NLP-based stock query engine  
- 📡 REST API backend for data processing  
- 🧩 Modular and scalable architecture  

---

## 🏗️ Project Architecture

The project follows a modular full-stack architecture:

### 🔹 Backend
- API server to handle client requests  
- NLP engine to process natural language queries  
- Database integration for financial datasets  

### 🔹 Dashboard
- Interactive UI for stock visualization  
- Market exploration and analytics views  
- Signal tracking and insights display  

### 🔹 Testing
- Backend smoke testing  
- Authentication validation  

---

## 🛠️ Tech Stack

### Frontend / Dashboard
- Python  
- Streamlit  

### Backend
- Python  
- REST APIs  

### Database
- SQLite  

### AI / NLP
- Natural Language Processing Engine  

---

## 📂 Project Structure

AI_stocklens/
│
├── backend/
│   ├── api_server.py
│   ├── nlp/
│   └── data/
│
├── dashboard/
│   ├── main.py
│   ├── services/
│   ├── views/
│   └── assets/
│
├── tests/
│   ├── auth_smoke.py
│   └── smoke_backend.py
│
└── json_output_code.py

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone <repository-url>
cd AI_stocklens
```

### 2️⃣ Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate      # For Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run Backend Server
```bash
python backend/api_server.py
```

### 5️⃣ Run Dashboard
```bash
streamlit run dashboard/main.py
```

---

## 📊 Usage Guide

1. Launch the dashboard in your browser.  
2. Explore stock data and financial indicators.  
3. Use the NLP query system to analyze stocks using natural language.  
4. Review signals, holdings, and market insights.  

---

## 🧪 Testing

Run backend smoke tests:
```bash
python tests/smoke_backend.py
```

Run authentication tests:
```bash
python tests/auth_smoke.py
```

---

## 🎯 Project Objective

The goal of this project is to develop an intelligent stock analytics platform that:

- Simplifies financial market analysis  
- Provides AI-driven stock insights  
- Enhances data-driven decision-making  

---

## 📌 Internship Context

This project was developed during the Infosys Springboard Internship as part of an industry-oriented AI and full-stack development initiative.

---

## 👩‍💻 Author

**Goli Sai Sri**
