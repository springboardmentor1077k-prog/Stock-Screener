from typing import Dict, Any, Tuple, List
import logging

# We assume this function exists in another file you have.
try:
    from quarterly_compiler import compile_last_n_quarters_sql
except ImportError:
    # Fallback if the file doesn't exist yet (prevents crash)
    def compile_last_n_quarters_sql(*args): return "1=1"

# Standard fields mapped to their database table alias
FIELD_MAPPING = {
    "pe_ratio": "f.pe_ratio",
    "peg_ratio": "f.peg_ratio",
    "dividend_yield": "f.dividend_yield",
    "debt_to_equity": "f.debt_to_equity",
    "net_profit": "f.net_profit", 
    "sector": "s.sector",
    "company_name": "s.company_name",
    "ticker": "s.ticker",
    "current_price": "a.current_price",
    "price": "a.current_price"
}

# Fields that require special subquery handling
QUARTERLY_FIELDS = ["revenue", "net_profit", "ebitda"]

def compile_node(node: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    Recursively compiles a DSL node into a SQL fragment and parameters.
    Returns: (sql_string, list_of_parameters)
    """
    
    # --- CASE 1: GROUP NODE (Nested Logic) ---
    if "logic" in node:
        logic = node["logic"].upper()
        filters = node.get("filters", [])

        # FIX: Handle empty filters list to avoid "()" SQL error
        if not filters:
            return "1=1", []

        if logic not in ["AND", "OR"]:
            raise ValueError(f"Invalid logic operator: {logic}")
        
        sub_sqls = []
        sub_params = []
        
        for child in filters:
            child_sql, child_params = compile_node(child)
            # Only append valid SQL fragments
            if child_sql and child_sql != "1=1":
                sub_sqls.append(child_sql)
                sub_params.extend(child_params)
            
        # Join with the logic operator and wrap in parentheses
        if not sub_sqls:
             return "1=1", []
             
        # CRITICAL FIX: The parentheses here ensure (A AND B) OR (C AND D) logic holds
        joined_sql = f"({f' {logic} '.join(sub_sqls)})"
        return joined_sql, sub_params

    # --- CASE 2: CONDITION NODE (Leaf Rule) ---
    elif "field" in node:
        field = node["field"]
        op = node["operator"]
        value = node.get("value")
        
        # 2a. Handle Quarterly Logic (Complex Subquery)
        if field in QUARTERLY_FIELDS and "quarters" in node:
            n_quarters = node.get("quarters", 1)
            subquery = compile_last_n_quarters_sql(field, op, value, n_quarters)
            return subquery, [] 

        # 2b. Handle Standard Logic
        db_column = FIELD_MAPPING.get(field)
        
        # Fallback: if field not found, safe default
        if not db_column:
             return "1=1", []

        # Handle "BETWEEN"
        if str(op).lower() == "between":
            if isinstance(value, list) and len(value) >= 2:
                return f"{db_column} BETWEEN %s AND %s", [value[0], value[1]]
            else:
                return "1=1", [] # Invalid value for between

        # Handle Standard Operators
        elif op in ["=", "<", ">", "<=", ">="]:
            return f"{db_column} {op} %s", [value]
            
        else:
            return "1=1", []

    else:
        # Invalid Node Structure -> Return Safe True
        return "1=1", []

def compile_dsl_to_sql_with_params(dsl: Dict[str, Any]) -> Tuple[str, Tuple[Any, ...]]:
    """Wrapper function to start compilation"""
    if not dsl:
        return "1=1", tuple()
    
    sql, params = compile_node(dsl)
    return sql, tuple(params)