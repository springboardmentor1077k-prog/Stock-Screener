from llm_integration import english_to_dsl
from validator import validate_dsl
from rule_compiler import compile_node
from db import get_db
from cache_utils import cached_query


@cached_query(ttl=300)
def run_query(user_query):
    try:
        # 1️⃣ Natural Language → DSL
        dsl = english_to_dsl(user_query)

        if dsl.get("invalid") is True:
            return {
                "status": "error",
                "message": "Invalid or unsupported query"
            }

        # 2️⃣ Validate DSL (recursive)
        valid, error = validate_dsl(dsl)
        if not valid:
            return {
                "status": "error",
                "message": error
            }

        # 3️⃣ Compile DSL → SQL WHERE clause
        params = []
        where_clause = compile_node(dsl, params)

        # 4️⃣ Final SQL (joins are deterministic)
        sql = f"""
        SELECT DISTINCT
            s.symbol,
            s.company_name,
            a.current_market_price AS cp,
            a.target_price_high AS tp,
            ROUND(
                CASE
                    WHEN a.current_market_price IS NULL OR a.current_market_price = 0 OR a.target_price_high IS NULL THEN NULL
                    ELSE ((a.target_price_high - a.current_market_price) / a.current_market_price) * 100
                END, 2
            ) AS upside_percent,
            CASE
                WHEN a.current_market_price IS NULL OR a.target_price_high IS NULL THEN 'NO_DATA'
                WHEN a.target_price_high >= a.current_market_price * 1.2 THEN 'BUY'
                WHEN a.target_price_high >= a.current_market_price * 1.05 THEN 'HOLD'
                ELSE 'SELL'
            END AS recommendation
        FROM stocks_master s
        JOIN fundamentals f ON s.id = f.stock_id
        LEFT JOIN analyst_targets a ON s.id = a.stock_id
        LEFT JOIN quarterly_financials q ON s.id = q.stock_id
        WHERE {where_clause}
        """
        
        # 5️⃣ Execute safely
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()


        # 6️⃣ Return response
        return {
            "status": "success",
            "count": len(rows),
            "rows": rows
        }
    
    except Exception as e:
        print(f"[ERROR] Exception in run_query: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Internal error: {str(e)}"
        }


