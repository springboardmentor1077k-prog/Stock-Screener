import yfinance as yf
import logging
import math
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Stock, Fundamental, QuarterlyFinancial, Alert

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. DATA CLEANING ---
def clean_num(val):
    """Converts NaN, Infinity, or non-numbers to None."""
    if val is None: return None
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val): return None
        return f_val
    except: return None

# --- 2. SMART VALUE EXTRACTOR (The Fix!) ---
def get_safe_value(df, date_col, possible_rows):
    """
    Tries to find a value by checking a list of possible row names.
    Example: checks ['Net Income', 'Net Income Common Stockholders']
    """
    for row_name in possible_rows:
        if row_name in df.index:
            try:
                # Get value for specific date column
                val = df.loc[row_name, date_col]
                clean_val = clean_num(val)
                if clean_val is not None:
                    return clean_val
            except Exception:
                continue
    return None

# --- 3. ALERT CHECKING ---
def check_alerts(db: Session, stock_id: int, current_price: float, symbol: str):
    alerts = db.query(Alert).filter(Alert.stock_id == stock_id, Alert.is_active == True).all()
    for alert in alerts:
        triggered = False
        if alert.condition_type == "price_above" and current_price > alert.target_value:
            triggered = True
        elif alert.condition_type == "price_below" and current_price < alert.target_value:
            triggered = True
            
        if triggered:
            logger.info(f"🔔 ALERT TRIGGERED: {symbol} is now {current_price}")
            alert.is_active = False 

# --- 4. QUARTERLY DATA UPDATE ---
def update_quarterly_data(db: Session, stock_id: int, ticker: yf.Ticker):
    try:
        q_fin = ticker.quarterly_financials
        if q_fin is None or q_fin.empty:
            return

        # Define possible names for metrics (Yahoo changes these often)
        keys_revenue = ['Total Revenue', 'Operating Revenue', 'Revenue']
        keys_profit = ['Net Income', 'Net Income Common Stockholders', 'Net Income From Continuing And Discontinued Operation', 'Net Income Continuous Operations']
        keys_eps = ['Basic EPS', 'Diluted EPS', 'Basic EPS', 'Earnings Per Share']
        keys_ebitda = ['EBITDA', 'Normalized EBITDA', 'EBIT', 'Operating Income']

        for date_obj in q_fin.columns:
            date_str = date_obj.strftime("%Y-%m-%d")
            
            # Use the "Key Hunter" function
            revenue = get_safe_value(q_fin, date_obj, keys_revenue)
            profit = get_safe_value(q_fin, date_obj, keys_profit)
            eps = get_safe_value(q_fin, date_obj, keys_eps)
            ebitda = get_safe_value(q_fin, date_obj, keys_ebitda)

            # Only save if we have at least Revenue OR Profit
            if not revenue and not profit:
                continue

            # Check if exists, if so UPDATE it, else INSERT
            existing = db.query(QuarterlyFinancial).filter(
                QuarterlyFinancial.stock_id == stock_id,
                QuarterlyFinancial.period_date == date_str
            ).first()

            if existing:
                existing.revenue = revenue
                existing.net_profit = profit
                existing.eps = eps
                existing.ebitda = ebitda
            else:
                db.add(QuarterlyFinancial(
                    stock_id=stock_id, 
                    period_date=date_str, 
                    revenue=revenue, 
                    net_profit=profit, 
                    eps=eps,
                    ebitda=ebitda
                ))
                
    except Exception as e:
        logger.warning(f"   ⚠️ Quarterly update skipped: {e}")

# --- 5. MAIN UPDATE LOOP ---
def update_market_data():
    db = SessionLocal()
    try:
        stocks = db.query(Stock).all()
        logger.info(f"🔄 Starting FULL update for {len(stocks)} stocks...")
        
        for stock in stocks:
            try:
                symbol_ns = f"{stock.symbol}.NS" if not stock.symbol.endswith(".NS") else stock.symbol
                ticker = yf.Ticker(symbol_ns)
                
                # A. Get Price & Fundamentals
                fast = getattr(ticker, "fast_info", {})
                info = ticker.info or {}
                
                price = clean_num(fast.get("last_price")) or clean_num(info.get("currentPrice"))
                pe = clean_num(info.get("trailingPE"))
                growth = clean_num(info.get("revenueGrowth"))
                peg = clean_num(info.get("pegRatio"))
                cap = clean_num(info.get("marketCap"))

                if peg is None and pe and growth and growth > 0:
                    try: peg = round(pe / (growth * 100), 2)
                    except: pass

                # B. Save Fundamentals
                if price:
                    fund = db.query(Fundamental).filter(Fundamental.stock_id == stock.id).first()
                    if fund:
                        fund.current_price = price
                        fund.pe_ratio = pe
                        fund.peg_ratio = peg
                        fund.revenue_growth_yoy = growth
                        fund.market_cap = cap
                        
                        check_alerts(db, stock.id, price, stock.symbol)
                        logger.info(f"   ✅ Updated {stock.symbol}: ₹{price}")
                    
                    # C. Update Quarterly (Now with Key Hunter!)
                    update_quarterly_data(db, stock.id, ticker)

            except Exception as e:
                logger.error(f"Failed {stock.symbol}: {e}")

        db.commit()
        logger.info("Update complete.")
        
    except Exception as e:
        logger.error(f"Critical Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_market_data()