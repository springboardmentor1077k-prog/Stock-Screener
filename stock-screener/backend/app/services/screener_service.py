import re
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.stock import Stock
from app.models.fundamentals import Fundamentals
from app.models.financials import Financials
from app.schemas.stock import ScreenerQuery, FilterCondition
from app.schemas.dsl import generate_dsl
from app.utils.dsl_mapper import map_dsl_to_screener_query

class ScreenerService:
    @staticmethod
    def log_query(db: Session, user_id: int, text: str, query_obj: ScreenerQuery):
        from app.models.screeener_run import UserQuery
        import json
        
        # Serialize only if it's a Pydantic model
        parsed = query_obj.dict() if hasattr(query_obj, 'dict') else query_obj
        
        log = UserQuery(
            user_id=user_id,
            raw_query_text=text,
            action=query_obj.action,
            parsed_dsl=parsed
        )
        db.add(log)
        db.commit()

    @staticmethod
    def parse_natural_language(query: str, db: Session = None, user_id: int = None) -> ScreenerQuery:
        """
        Parses natural language queries using the DSL parser.
        
        Examples:
            "PE below 20" -> screen with PE < 20
            "Give stock price of Infosys" -> get_price action
            "ROE above 15 and debt to equity below 0.5" -> screen with multiple conditions
        """
        
        # --- Intent Detection: Check for "Get Price" queries ---
        query_lower = query.lower()
        price_patterns = [
            r"price of\s+(.*)", r"value of\s+(.*)", 
            r"how much is\s+(.*)", r"quote for\s+(.*)",
            r"stock price of\s+(.*)"
        ]
        
        for pat in price_patterns:
            match = re.search(pat, query_lower)
            if match:
                target = match.group(1).strip().strip("?")
                resulting_query = ScreenerQuery(action="get_price", target_symbol=target)
                
                # Log and return early
                if db and user_id:
                    ScreenerService.log_query(db, user_id, query, resulting_query)
                return resulting_query
        
        # --- Screening Intent: Use DSL Parser ---
        try:
            # Parse query using DSL
            dsl_result = generate_dsl(query)
            
            # Check for parsing errors
            if "error" in dsl_result:
                # Fallback to empty conditions with global search
                final_result = ScreenerQuery(
                    action="screen",
                    conditions=[],
                    global_search=query
                )
            else:
                # Convert DSL conditions to ScreenerQuery format
                conditions = map_dsl_to_screener_query(dsl_result)
                final_result = ScreenerQuery(
                    action="screen",
                    conditions=conditions,
                    global_search=None
                )
        
        except Exception as e:
            # If DSL parsing fails, fallback to global search
            final_result = ScreenerQuery(
                action="screen",
                conditions=[],
                global_search=query
            )
        
        # Log the query
        if db and user_id:
            ScreenerService.log_query(db, user_id, query, final_result)
        
        return final_result

    @staticmethod
    def execute_query(db: Session, query: ScreenerQuery) -> List[Stock]:
        
        # --- Handle "Get Price" Intent (Alpha Vantage Real-time + Auto Store) ---
        if query.action == "get_price" and query.target_symbol:
            import requests
            
            # Use Alpha Vantage API Key
            API_KEY = "6D3G16MS0154LRXP"
            USD_TO_INR = 83.0
            
            symbol = query.target_symbol.upper()
            # Handle common Indian stock patterns
            if "." not in symbol:
                symbol = f"{symbol}.BSE"  # Default to BSE for Alpha Vantage coverage
                
            try:
                # 1. Fetch Alpha Vantage OVERVIEW (for fundamentals + currency)
                overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
                overview_res = requests.get(overview_url)
                over_data = overview_res.json() if overview_res.status_code == 200 else {}
                
                # 2. Fetch Alpha Vantage GLOBAL_QUOTE (for real-time price)
                quote_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
                quote_res = requests.get(quote_url)
                quote_data = quote_res.json().get("Global Quote", {}) if quote_res.status_code == 200 else {}
                
                price = float(quote_data.get("05. price", 0.0))
                currency = over_data.get("Currency", "INR")
                
                if price > 0:
                    final_price = price * USD_TO_INR if currency == "USD" else price
                    
                    # --- AUTO STORE/UPDATE IN DB ---
                    db_stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                    if not db_stock:
                        db_stock = Stock(
                            symbol=symbol,
                            company_name=over_data.get("Name", symbol),
                            sector=over_data.get("Sector", "Unknown"),
                            industry=over_data.get("Industry", "Unknown"),
                            exchange=over_data.get("Exchange", "BSE"),
                            market_cap=float(over_data.get("MarketCapitalization", 0)) * (USD_TO_INR if currency == "USD" else 1),
                            status="ACTIVE"
                        )
                        db.add(db_stock)
                        db.flush()
                    else:
                        db_stock.market_cap = float(over_data.get("MarketCapitalization", 0)) * (USD_TO_INR if currency == "USD" else 1)
                    
                    fund = db.query(Fundamentals).filter(Fundamentals.stock_id == db_stock.id).first()
                    if not fund:
                        fund = Fundamentals(
                            stock_id=db_stock.id,
                            current_price=final_price,
                            pe_ratio=float(over_data.get("TrailingPE", 0.0)),
                            market_cap=db_stock.market_cap,
                            div_yield=float(over_data.get("DividendYield", 0.0)) * 100
                        )
                        db.add(fund)
                    else:
                        fund.current_price = final_price
                        fund.pe_ratio = float(over_data.get("TrailingPE", 0.0))
                        fund.market_cap = db_stock.market_cap
                    
                    db.commit()
                    # Refresh to return full object with relationships
                    db.refresh(db_stock)
                    return [db_stock]
            except Exception as e:
                print(f"Error in Alpha Vantage auto-store: {e}")
                pass
            
            # DB Search Fallback
            db_stock = db.query(Stock).filter(Stock.symbol.ilike(f"%{query.target_symbol}%")).first()
            if not db_stock:
                db_stock = db.query(Stock).filter(Stock.company_name.ilike(f"%{query.target_symbol}%")).first()
            
            return [db_stock] if db_stock else []

        # --- Handle "Screen" Intent (Database Filter) ---
        # Start query on Stock, join Fundamentals ensure we can filter both
        sql_query = db.query(Stock).join(Fundamentals) # (so we don't lose stocks without financials if not filtering by them)
        # However, looking at the schema, it's safer to just join if needed.
        # For simplicity, we'll join all potential tables or dynamically join.
        # Let's start with Stock and join Fundamentals (One-to-One).
        
        # sql_query = db.query(Stock).join(Fundamentals) # This line was duplicated in the instruction, removing one.
        
        # Check if we need to join Financials (One-to-Many). 
        # CAUTION: One-to-Many join (Stock -> Financials) will return multiple rows per stock!
        # We need to filter on the LATEST financial record or aggregate.
        # For this MVP, let's assume we filter on ANY financial record matching.
        # Ideally, we should filter on the latest quarter.
        
        joined_financials = False
        
        expressions = []
        
        # 1. Apply Specific Conditions
        for condition in query.conditions:
            # Determine if field belongs to Stock, Fundamentals, or Financials
            model = None
            if hasattr(Stock, condition.field):
                model = Stock
            elif hasattr(Fundamentals, condition.field):
                model = Fundamentals
            elif hasattr(Financials, condition.field):
                model = Financials
                if not joined_financials:
                    sql_query = sql_query.join(Financials)
                    joined_financials = True
            
            if model:
                column = getattr(model, condition.field)
                val = condition.value
                
                if condition.operator == ">":
                    expressions.append(column > val)
                elif condition.operator == "<":
                    expressions.append(column < val)
                elif condition.operator == ">=":
                    expressions.append(column >= val)
                elif condition.operator == "<=":
                    expressions.append(column <= val)
                elif condition.operator == "==":
                    expressions.append(column == val)
                elif condition.operator == "ilike":
                    expressions.append(column.ilike(f"%{val}%"))
        
        # 2. Apply Global Search (if any)
        if query.global_search:
            term = f"%{query.global_search}%"
            # Search Symbol or Name or Sector
            expressions.append(
                (Stock.symbol.ilike(term)) | 
                (Stock.company_name.ilike(term)) | 
                (Stock.sector.ilike(term))
            )

        if expressions:
            sql_query = sql_query.filter(and_(*expressions))
            
        return sql_query.distinct().all() # distinct() to avoid duplicates if multiple financials match
