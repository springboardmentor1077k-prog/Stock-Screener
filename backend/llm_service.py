import os
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import and_, func, desc, asc, case
from sqlalchemy.orm import Session
from .models import Stock, Fundamental, QuarterlyFinancial

# Setup
load_dotenv()
logger = logging.getLogger(__name__)

# Map English terms to Database Columns
FIELD_MAP = {
    "sector": Stock.sector,
    "symbol": Stock.symbol,
    "company": Stock.company_name,
    "pe": Fundamental.pe_ratio,
    "peg": Fundamental.peg_ratio,
    "price": Fundamental.current_price,
    "market_cap": Fundamental.market_cap,
    "debt_to_fcf": Fundamental.debt_to_fcf,
    "revenue_growth": Fundamental.revenue_growth_yoy,
}

class LLMQueryParser:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

    def parse_query(self, user_text: str):
        """
        Translates natural language strictly into Market Screener JSON.
        """
        # 1. Guard against empty queries
        if not user_text or not user_text.strip():
            return None

        system_prompt = """
        You are a smart Query Translator for a Stock Screener. 
        Your job is to convert English questions into JSON filters.

        ### RULES:
        1. If the user mentions a specific company name or symbol (e.g., "TCS", "Infosys", "Reliance"), create a filter for 'symbol'.
        2. If the user asks for a Sector (e.g., "IT", "Banks"), create a filter for 'sector' with 'contains'.
        3. Map "IT" -> "Technology", "Banks" -> "Financial Services".

        ### EXAMPLES (Follow these patterns):
        
        User: "Show me TCS"
        Output: {"filters": [{"field": "symbol", "op": "=", "value": "TCS"}]}

        User: "TCS stock details"
        Output: {"filters": [{"field": "symbol", "op": "=", "value": "TCS"}]}

        User: "IT stocks with PE below 25"
        Output: {"filters": [{"field": "sector", "op": "contains", "value": "Technology"}, {"field": "pe", "op": "<", "value": 25}]}

        User: "Cheap stocks"
        Output: {"filters": [{"field": "pe", "op": "<", "value": 15}]}

        Now, convert the user's latest query to JSON.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.0  # Make it deterministic (less creative)
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"LLM Parsing Error: {e}")
            return None

class ScreenerEngine:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, query_json: dict):
        if not query_json or "filters" not in query_json:
            return {"message": "I didn't understand that query."}

        # Start Query
        query = self.db.query(Stock, Fundamental).join(Fundamental)
        
        for f in query_json.get("filters", []):
            field = f.get("field")
            val = f.get("value")
            # Default op to '=' for exact matches (like symbols), 'contains' for text
            default_op = "="
            
            op = f.get("op", default_op)

            # 1. Handle Quarterly Trends
            if field == "quarterly_trend":
                metric = getattr(QuarterlyFinancial, f.get("metric", "net_profit"))
                quarters = int(f.get("quarters", 4))
                
                sq = self.db.query(
                    QuarterlyFinancial.stock_id,
                    metric.label('val'),
                    func.row_number().over(partition_by=QuarterlyFinancial.stock_id, order_by=desc(QuarterlyFinancial.period_date)).label('rn')
                ).subquery()

                cond = (sq.c.val > val) if op == ">" else (sq.c.val < val)
                
                trend = self.db.query(sq.c.stock_id)\
                    .filter(sq.c.rn <= quarters)\
                    .group_by(sq.c.stock_id)\
                    .having(and_(func.count(sq.c.rn) == quarters, func.sum(case((cond, 1), else_=0)) == quarters))\
                    .subquery()

                query = query.filter(Stock.id.in_(trend))
                continue

            # 2. Handle Standard Filters
            col = FIELD_MAP.get(field)
            if col:
                # Case-Insensitive Search for Symbols and Sectors
                if field in ["symbol", "sector", "company"] and isinstance(val, str):
                    if op == "contains" or op == "=":
                         query = query.filter(col.ilike(f"%{val}%"))
                
                # Number filters
                elif op == ">": query = query.filter(col > val)
                elif op == "<": query = query.filter(col < val)
                elif op == ">=": query = query.filter(col >= val)
                elif op == "<=": query = query.filter(col <= val)
                elif op == "=": query = query.filter(col == val)

        results = query.limit(20).all()
        
        if not results:
            return {"message": "No stocks found matching those criteria."}

        return [{"symbol": s.symbol, "company": s.company_name, "price": f.current_price, "pe": f.pe_ratio, "sector": s.sector} for s, f in results]
