import re
import json
import logging
import os
import requests
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Depends, status
from jose import jwt, JWTError

from fastapi.security import OAuth2PasswordBearer
from app.core import settings, get_password_hash, verify_password, create_access_token
from app.db import fetch_all, fetch_one, insert_returning, execute_query, get_db_connection, get_db
from app.schemas import (
    UserCreate, UserLogin, PortfolioItemCreate, 
    ScreenerQuery, FilterCondition, StockResponse
)

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# --- REPOSITORIES ---

class UserRepository:
    @staticmethod
    def get_user_by_email(conn, email: str) -> Optional[Dict[str, Any]]:
        query = 'SELECT id, email, hashed_password, is_active, is_superuser FROM "user" WHERE email = %s'
        return fetch_one(query, (email,))

    @staticmethod
    def create_user(conn, user: UserCreate) -> Dict[str, Any]:
        hashed_password = get_password_hash(user.password)
        query = 'INSERT INTO "user" (email, hashed_password, is_active, is_superuser) VALUES (%s, %s, %s, %s) RETURNING id, email, hashed_password, is_active, is_superuser'
        return insert_returning(query, (user.email, hashed_password, True, False))

class PortfolioRepository:
    @staticmethod
    def add_to_portfolio(conn, user_id: int, item_in: PortfolioItemCreate) -> Dict[str, Any]:
        query = "INSERT INTO portfolio (user_id, stock_id, quantity, avg_price) VALUES (%s, %s, %s, %s) RETURNING id, user_id, stock_id, quantity, avg_price"
        return insert_returning(query, (user_id, item_in.stock_id, item_in.quantity, item_in.avg_price))

    @staticmethod
    def get_portfolio(conn, user_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT p.id, p.user_id, p.stock_id, p.quantity, p.avg_price,
                   s.id as s_id, s.symbol, s.company_name, s.sector, s.industry, s.exchange
            FROM portfolio p
            JOIN stock s ON p.stock_id = s.id
            WHERE p.user_id = %s
        """
        results = fetch_all(query, (user_id,))
        portfolio = []
        for row in results:
            portfolio.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "stock_id": row["stock_id"],
                "quantity": row["quantity"],
                "avg_price": row["avg_price"],
                "stock": {
                    "id": row["s_id"],
                    "symbol": row["symbol"],
                    "company_name": row["company_name"],
                    "sector": row["sector"],
                    "industry": row["industry"],
                    "exchange": row["exchange"]
                }
            })
        return portfolio

    @staticmethod
    def remove_from_portfolio(conn, user_id: int, stock_id: int) -> bool:
        with get_db_connection() as connection:
            with connection.cursor() as cur:
                query = "DELETE FROM portfolio WHERE user_id = %s AND stock_id = %s RETURNING id"
                cur.execute(query, (user_id, stock_id))
                return cur.fetchone() is not None

# --- DSL MAPPER ---

DSL_TO_DB_FIELD_MAP = {
    "PE": "pe_ratio", "PB": "pb_ratio", "PS": "ps_ratio", "PEG": "peg_ratio",
    "MARKET_CAP": "market_cap", "ROE": "roe", "ROA": "roa", "ROCE": "roce",
    "DEBT_EQUITY": "debt_to_equity", "CURRENT_RATIO": "current_ratio",
    "QUICK_RATIO": "quick_ratio", "DIVIDEND_YIELD": "div_yield",
    "PRICE": "current_price", "VOLUME": "volume", "REVENUE": "revenue_generated",
    "EBITDA": "ebitda", "NET_PROFIT": "net_profit", "PROFIT": "net_profit"
}

def map_dsl_to_screener_query(dsl_result: Dict[str, Any]) -> List[FilterCondition]:
    if "error" in dsl_result: raise ValueError(f"DSL parsing error: {dsl_result['error']}")
    conditions = []
    for cond in dsl_result.get("conditions", []):
        if cond.get("type") == "quarterly":
            q_condition = cond.get("condition", "positive").upper()
            conditions.append(FilterCondition(field=cond.get("field"), operator=f"QUARTERLY_{q_condition}", value=cond.get("last_n", 1)))
        else:
            field, operator, value = cond.get("field"), cond.get("operator"), cond.get("value")
            if field and operator and value is not None:
                conditions.append(FilterCondition(field=field, operator=operator, value=value))
    return conditions

# --- SERVICES ---

class AuthService:
    @staticmethod
    def signup(conn, user_in: UserCreate):
        if UserRepository.get_user_by_email(conn, user_in.email):
            raise HTTPException(status_code=400, detail="The user with this email already exists in the system.")
        return UserRepository.create_user(conn, user_in)

    @staticmethod
    def login(conn, user_in: UserLogin):
        user = UserRepository.get_user_by_email(conn, user_in.email)
        if not user or not verify_password(user_in.password, user["hashed_password"]):
            return None
        return create_access_token(subject=user["email"])

class GeminiNLPService:
    def __init__(self):
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not configured. NLP disabled.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_dsl_from_text(self, text: str) -> dict:
        if not self.model: return {"error": "Gemini API key not configured"}
        prompt = f"""You are a query translator. Convert user request to JSON DSL.
        Allowed Snapshot fields: pe_ratio, peg_ratio, pb_ratio, market_cap, promoter_holding, debt_to_equity, roe, roce.
        Quarterly fields: revenue, ebitda, net_profit.
        Snapshot condition format: {{ "field": "<field>", "operator": "<op>", "value": <num> }}
        Quarterly format: {{ "field": "<field>", "type": "quarterly", "last_n": <n>, "condition": "<pos/neg/inc/dec>" }}
        Output JSON ONLY. User: "{text}" """
        try:
            response = self.model.generate_content(prompt)
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean_text)
            return data
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {"error": str(e)}

class ScreenerService:
    @staticmethod
    def log_query(conn, user_id: int, text: str, query_obj: ScreenerQuery):
        try:
            parsed = query_obj.dict() if hasattr(query_obj, 'dict') else query_obj
            query = 'INSERT INTO userquery (user_id, raw_query_text, action, parsed_dsl) VALUES (%s, %s, %s, %s)'
            execute_query(query, (user_id, text, query_obj.action, json.dumps(parsed)))
        except Exception as e: logger.warning(f"Could not log query: {e}")

    @staticmethod
    def parse_natural_language(query: str, conn = None, user_id: int = None) -> ScreenerQuery:
        query_lower = query.lower()
        if any(re.search(pat, query_lower) for pat in [r"price of\s+(.*)", r"value of\s+(.*)", r"stock price of\s+(.*)"]):
            match = re.search(r"(?:price of|value of|stock price of)\s+(.*)", query_lower)
            target = match.group(1).strip().strip("?") if match else "UNKNOWN"
            resulting_query = ScreenerQuery(action="get_price", target_symbol=target)
            if conn and user_id: ScreenerService.log_query(conn, user_id, query, resulting_query)
            return resulting_query
        
        try:
            dsl_result = GeminiNLPService().generate_dsl_from_text(query)
            if "error" in dsl_result: final_result = ScreenerQuery(action="screen", conditions=[], global_search=query)
            else: final_result = ScreenerQuery(action="screen", conditions=map_dsl_to_screener_query(dsl_result), global_search=None)
        except Exception: final_result = ScreenerQuery(action="screen", conditions=[], global_search=query)
        
        if conn and user_id: ScreenerService.log_query(conn, user_id, query, final_result)
        return final_result

    @staticmethod
    def execute_query(conn, query: ScreenerQuery) -> List[Dict[str, Any]]:
        # This is a large method, I'll keep the logic but condense whitespace
        if query.action == "get_price" and query.target_symbol:
            # Alpha Vantage logic remains original as in screener_service.py
            API_KEY = "6D3G16MS0154LRXP"
            USD_TO_INR = 83.0
            symbol = query.target_symbol.upper()
            if "." not in symbol: symbol = f"{symbol}.BSE"
            try:
                over_data = requests.get(f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}").json()
                quote_data = requests.get(f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}").json().get("Global Quote", {})
                price = float(quote_data.get("05. price", 0.0))
                if price > 0:
                    currency = over_data.get("Currency", "INR")
                    final_price = price * USD_TO_INR if currency == "USD" else price
                    market_cap = float(over_data.get("MarketCapitalization", 0)) * (USD_TO_INR if currency == "USD" else 1)
                    with get_db_connection() as connection:
                        with connection.cursor() as cur:
                            cur.execute("SELECT id FROM stock WHERE symbol = %s", (symbol,))
                            stock_row = cur.fetchone()
                            if not stock_row:
                                cur.execute("INSERT INTO stock (symbol, company_name, sector, industry, exchange, market_cap, status) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id", (symbol, over_data.get("Name", symbol), over_data.get("Sector", "Unknown"), over_data.get("Industry", "Unknown"), over_data.get("Exchange", "BSE"), market_cap, "ACTIVE"))
                                stock_id = cur.fetchone()[0]
                            else:
                                stock_id = stock_row[0]
                                cur.execute("UPDATE stock SET market_cap = %s WHERE id = %s", (market_cap, stock_id))
                            cur.execute("SELECT id FROM fundamentals WHERE stock_id = %s", (stock_id,))
                            if not cur.fetchone(): cur.execute("INSERT INTO fundamentals (stock_id, current_price, pe_ratio, market_cap, div_yield) VALUES (%s, %s, %s, %s, %s)", (stock_id, final_price, float(over_data.get("TrailingPE", 0.0)), market_cap, float(over_data.get("DividendYield", 0.0)) * 100))
                            else: cur.execute("UPDATE fundamentals SET current_price = %s, pe_ratio = %s, market_cap = %s WHERE stock_id = %s", (final_price, float(over_data.get("TrailingPE", 0.0)), market_cap, stock_id))
                    return [fetch_one("SELECT * FROM stock WHERE symbol = %s", (symbol,))]
            except Exception as e: logger.error(f"Alpha Vantage error: {e}")
            stock_data = fetch_one("SELECT * FROM stock WHERE symbol ILIKE %s OR company_name ILIKE %s", (f"%{query.target_symbol}%", f"%{query.target_symbol}%"))
            return [stock_data] if stock_data else []

        # Select explicit columns to avoid ambiguous 'id' and ensure we get fundamentals
        sql_parts = ["""
            SELECT s.id, s.symbol, s.company_name, s.sector, s.industry, s.exchange,
                   f.id as fund_id, f.market_cap, f.pe_ratio, f.div_yield, f.current_price, f.last_updated
            FROM stock s
        """]
        joins = ["LEFT JOIN fundamentals f ON s.id = f.stock_id"]
        where_conditions, params = [], []

        for cond in query.conditions:
            if cond.field in ['pe_ratio', 'pb_ratio', 'div_yield', 'current_price', 'roe', 'roce', 'debt_to_equity']:
                # fundamentals join is already default now
                where_conditions.append(f"f.{cond.field} {cond.operator} %s")
                params.append(cond.value)
            elif cond.field in ['revenue', 'net_profit', 'ebitda']:
                if "LEFT JOIN financials fin" not in " ".join(joins): joins.append("LEFT JOIN financials fin ON s.id = fin.stock_id")
                where_conditions.append(f"fin.{cond.field} {cond.operator} %s")
                params.append(cond.value)
        
        if query.global_search:
            term = f"%{query.global_search}%"
            where_conditions.append("(s.symbol ILIKE %s OR s.company_name ILIKE %s OR s.sector ILIKE %s)")
            params.extend([term, term, term])
        
        final_query = f"{' '.join(sql_parts)} {' '.join(joins)} {'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''}"
        
        raw_results = fetch_all(final_query, tuple(params) if params else None)
        
        # Restructure for StockResponse schema
        structured_results = []
        for row in raw_results:
            stock_data = {
                "id": row["id"],
                "symbol": row["symbol"],
                "company_name": row["company_name"],
                "sector": row["sector"],
                "industry": row["industry"],
                "exchange": row["exchange"],
                "fundamentals": None
            }
            
            if row.get("fund_id"):
                stock_data["fundamentals"] = {
                    "id": row["fund_id"],
                    "market_cap": row["market_cap"],
                    "pe_ratio": row["pe_ratio"],
                    "div_yield": row["div_yield"],
                    "current_price": row["current_price"],
                    "last_updated": row["last_updated"]
                }
            
            structured_results.append(stock_data)
            
        return structured_results

class PortfolioService:
    @staticmethod
    def add_stock(conn, user_id: int, item_in: PortfolioItemCreate) -> Dict[str, Any]:
        if fetch_one("SELECT id FROM portfolio WHERE user_id = %s AND stock_id = %s", (user_id, item_in.stock_id)):
            raise HTTPException(status_code=400, detail="Stock already in portfolio")
        
        added_item = PortfolioRepository.add_to_portfolio(conn, user_id, item_in)
        
        # Fetch stock details to satisfy schema
        stock = fetch_one("SELECT id, symbol, company_name, sector, industry, exchange FROM stock WHERE id = %s", (item_in.stock_id,))
        if stock:
            added_item["stock"] = stock
            
        return added_item

    @staticmethod
    def get_user_portfolio(conn, user_id: int) -> List[Dict[str, Any]]:
        return PortfolioRepository.get_portfolio(conn, user_id)

    @staticmethod
    def remove_stock(conn, user_id: int, stock_id: int):
        if not PortfolioRepository.remove_from_portfolio(conn, user_id, stock_id):
            raise HTTPException(status_code=404, detail="Stock not found in portfolio")
        return {"status": "success"}

# --- DEPENDENCIES ---

def get_current_user(conn = Depends(get_db), token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError: raise credentials_exception
    user = UserRepository.get_user_by_email(conn, email=email)
    if user is None: raise credentials_exception
    return user
