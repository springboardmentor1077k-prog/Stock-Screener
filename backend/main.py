import os
import logging
import math
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from dotenv import load_dotenv

from .database import SessionLocal, init_db
from .models import User, Stock, Portfolio, PortfolioItem, Alert, Fundamental
from .llm_service import LLMQueryParser, ScreenerEngine
from .ingestion import update_market_data

from backend.database import redis_client
import json

# 1. Config & Setup
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.on_event("startup")
def on_startup():
    init_db()

# 2. Auth Utilities
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise HTTPException(401, "Invalid token")
    except JWTError: raise HTTPException(401, "Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None: raise HTTPException(401, "User not found")
    return user

# 3. Pydantic Models
class UserAuth(BaseModel):
    username: str
    password: str

class ScreenerRequest(BaseModel):
    query: str

class PortfolioAddRequest(BaseModel):
    symbol: str
    quantity: float
    buy_price: float
    
class PortfolioSellRequest(BaseModel):
    symbol: str
    quantity: float
    sell_price: float

class AlertRequest(BaseModel):
    symbol: str
    condition: str
    value: float

def clean_float(val):
    if val is None:
        return None
    if math.isnan(val) or math.isinf(val):
        return None
    return val

# 4. API Routes

# --- AUTH ---
@app.post("/register")
def register(user: UserAuth, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(400, "User already exists")
    hashed_pw = pwd_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Create default portfolio for new user
    db.add(Portfolio(user_id=new_user.id, name="My Portfolio"))
    db.commit()
    return {"message": "User created successfully"}

@app.post("/login")
def login(user: UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    token = jwt.encode({"sub": db_user.username, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

# --- AI SCREENER (Cached with Redis) ---
@app.post("/screener/query")
def run_screener(req: ScreenerRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 1. Create a "Cache Key" based on the user's text
    # We lowercase and strip spaces
    clean_query = req.query.strip().lower()
    cache_key = f"screener_query:{clean_query}"

    # 2. CHECK REDIS
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            print(f"Serving '{clean_query}' from Redis Cache")
            return json.loads(cached_data)
    except Exception as e:
        print(f"Redis Error: {e}")

    # 3. QUERY LLM & DATABASE
    print(f"Asking LLM & Querying DB for '{clean_query}'...")
    parser = LLMQueryParser()
    query_json = parser.parse_query(req.query)
    
    if not query_json:
        result_data = {"interpretation": None, "results": {"message": "I couldn't interpret that market query."}}
        return result_data
    
    engine = ScreenerEngine(db) 
    results = engine.execute(query_json)
    
    # Structure the final response
    result_data = {"interpretation": query_json, "results": results}

    # 4. SAVE TO REDIS (For next time)
    try:
        # ex=300 means cache it for 5 minutes. 
        # We cache searches longer than live prices to save LLM costs!
        redis_client.set(cache_key, json.dumps(result_data), ex=300)
    except Exception as e:
        print(f"⚠️ Could not save to Redis: {e}")

    return result_data

# --- GET ALL STOCKS (Cached with Redis) ---
@app.get("/stocks")
def get_stocks(db: Session = Depends(get_db)):
    # 1. CHECK REDIS
    # We look for a key named "all_stocks_cache"
    try:
        cached_data = redis_client.get("all_stocks_cache")
        if cached_data:
            print("Serving from Redis Cache")
            return json.loads(cached_data)
    except Exception as e:
        print(f"Redis Error: {e}")
        cached_data = None # Fallback to database if Redis is down

    # 2. QUERY DATABASE
    print("Querying Database...")
    stocks = db.query(Stock).all()
    
    results = []
    for s in stocks:
        fund = s.fundamentals
        results.append({
            "id": s.id,
            "symbol": s.symbol,
            "company": s.company_name,
            "sector": s.sector,
            "price": fund.current_price if fund else None,
            "pe": fund.pe_ratio if fund else None,
            "growth": fund.revenue_growth_yoy if fund else None,
            "peg": fund.peg_ratio if fund else None,
            "market_cap": fund.market_cap if fund else None
        })

    # 3. SAVE TO REDIS (For next time)
    try:
        # ex=60 means "Expire in 60 seconds". Adjust this if you want it cached longer!
        redis_client.set("all_stocks_cache", json.dumps(results), ex=300)
    except Exception as e:
        print(f"Could not save to Redis: {e}")
    
    return results

# --- STOCK DETAILS (Cached with Redis) ---
@app.get("/stocks/{symbol}")
def get_stock_details(symbol: str, db: Session = Depends(get_db)):
    cache_key = f"stock_details:{symbol}"

    # 1. CHECK REDIS
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            print(f"Serving {symbol} details from Redis Cache")
            return json.loads(cached_data)
    except Exception as e:
        print(f"Redis Error: {e}")

    # 2. QUERY DATABASE
    print(f"Querying Database for {symbol}...")
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(404, "Stock not found")

    # Prepare Data
    fund = stock.fundamentals
    quarters = []
    if stock.quarterly_financials:
        quarters = sorted(stock.quarterly_financials, key=lambda x: x.period_date, reverse=True)

    # Build the response dictionary
    response_data = {
        "info": {
            "symbol": stock.symbol,
            "company": stock.company_name,
            "sector": stock.sector
        },
        "fundamentals": {
            "current_price": clean_float(fund.current_price) if fund else None,
            "pe_ratio": clean_float(fund.pe_ratio) if fund else None,
            "peg_ratio": clean_float(fund.peg_ratio) if fund else None,
            "market_cap": clean_float(fund.market_cap) if fund else None,
            "debt_to_fcf": clean_float(fund.debt_to_fcf) if fund else None,
            "revenue_growth": clean_float(fund.revenue_growth_yoy) if fund else None,
            "promoter_holding": clean_float(fund.promoter_holding) if fund else None
        },
        "quarterly": [
            {
                "date": str(q.period_date),
                "revenue": clean_float(q.revenue),
                "profit": clean_float(q.net_profit),
                "eps": clean_float(q.eps)
            } for q in quarters
        ]
    }

    # 3. SAVE TO REDIS
    try:
        # Cache individual stock details for 60 seconds
        redis_client.set(cache_key, json.dumps(response_data), ex=60)
    except Exception as e:
        print(f"Could not save to Redis: {e}")

    return response_data

# --- PORTFOLIO (Manual Management) ---
@app.get("/portfolio")
def get_portfolio(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    port = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not port: return []
    
    items = db.query(PortfolioItem).filter(PortfolioItem.portfolio_id == port.id).all()
    output = []
    for item in items:
        # Get live price from Fundamentals table
        cur_price = item.stock.fundamentals.current_price if item.stock.fundamentals else 0.0
        val = cur_price * item.quantity
        cost = item.buy_price * item.quantity
        pl = val - cost
        pl_pct = (pl / cost * 100) if cost > 0 else 0
        
        output.append({
            "symbol": item.stock.symbol,
            "qty": item.quantity,
            "avg_price": item.buy_price,
            "cur_price": cur_price,
            "value": round(val, 2),
            "p&l": round(pl, 2),
            "p&l%": f"{pl_pct:.2f}%"
        })
    return output

@app.post("/portfolio/add")
def add_to_portfolio(req: PortfolioAddRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    port = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    # Check for symbol with or without .NS
    stock = db.query(Stock).filter(Stock.symbol == req.symbol.replace(".NS", "")).first()
    
    if not stock:
        raise HTTPException(404, detail=f"Stock {req.symbol} not found. Try running Admin Refresh.")
        
    db.add(PortfolioItem(portfolio_id=port.id, stock_id=stock.id, quantity=req.quantity, buy_price=req.buy_price))
    db.commit()
    return {"message": "Added to portfolio"}

@app.post("/portfolio/sell")
def sell_portfolio_stock(req: PortfolioSellRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 1. Get User's Portfolio
    port = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not port:
        raise HTTPException(404, "Portfolio not found")

    # 2. Find the Stock
    # Try exact match or .NS suffix
    stock = db.query(Stock).filter(Stock.symbol == req.symbol.replace(".NS", "")).first()
    if not stock:
         stock = db.query(Stock).filter(Stock.symbol == f"{req.symbol}.NS").first()
    
    if not stock:
        raise HTTPException(404, "Stock not found in database")

    # 3. Find the Holding
    item = db.query(PortfolioItem).filter(
        PortfolioItem.portfolio_id == port.id,
        PortfolioItem.stock_id == stock.id
    ).first()

    if not item:
        raise HTTPException(400, f"You don't own {req.symbol}")

    # 4. Check Quantity
    if req.quantity > item.quantity:
        raise HTTPException(400, f"Cannot sell {req.quantity}. You only have {item.quantity}.")

    # 5. Calculate Profit/Loss (For your reference)
    profit = (req.sell_price - item.buy_price) * req.quantity

    # 6. Execute Sell
    if req.quantity == item.quantity:
        # Full Sell -> Delete the row
        db.delete(item)
        msg = f"Sold all {req.symbol}. Realized P&L: ₹{profit:,.2f}"
    else:
        # Partial Sell -> Reduce quantity
        item.quantity -= req.quantity
        msg = f"Sold {req.quantity} of {req.symbol}. Remaining: {item.quantity}. Realized P&L: ₹{profit:,.2f}"

    db.commit()
    return {"message": msg, "realized_pl": profit}

# --- ALERTS ---
@app.post("/alerts")
def create_alert(req: AlertRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stock = db.query(Stock).filter(Stock.symbol == req.symbol.replace(".NS", "")).first()
    if not stock: raise HTTPException(404, "Stock not found")
    db.add(Alert(user_id=user.id, stock_id=stock.id, condition_type=req.condition, target_value=req.value))
    db.commit()
    return {"message": "Alert set"}

@app.get("/alerts")
def get_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alerts = db.query(Alert).filter(Alert.user_id == user.id).all()
    return [{"id": a.id, "symbol": a.stock.symbol, "condition": a.condition_type, "target": a.target_value, "active": a.is_active} for a in alerts]

# --- DELETE ALERT
@app.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 1. Find the alert belonging to this user
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user.id).first()
    
    if not alert:
        raise HTTPException(404, "Alert not found.")
    
    # 2. Delete it
    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted successfully"}

# --- ADMIN ---
@app.post("/admin/refresh")
def refresh_data(bg_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    if user.username != "admin": raise HTTPException(403, "Admins only")
    bg_tasks.add_task(update_market_data)
    return {"message": "Refresh started"}
