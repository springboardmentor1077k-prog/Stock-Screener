from backend.logic.llm_parser import parse_to_dsl
from backend.logic.compiler import compile_sql
from backend.logic.validator import is_safe_query
from database.connection import get_db_connection


def run_screener(user_input: str):
    """Run the stock screener with natural language query."""
    try:
        # Parse user query to DSL
        dsl = parse_to_dsl(user_input)
        
        # Compile to SQL
        sql, params = compile_sql(dsl)
        
        # Validate SQL safety
        is_safe, msg = is_safe_query(sql)
        if not is_safe:
            return {"error": msg}
        
        # Execute query
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convert to list of dicts
        return [dict(row) for row in results]
    
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}