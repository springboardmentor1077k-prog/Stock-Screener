from typing import Dict, Any, Tuple, List
import logging
from quarterly_compiler import compile_last_n_quarters_sql

# Standard fields mapped to their database table alias
FIELD_MAPPING = {
    "pe_ratio": "f.pe_ratio",
    "peg_ratio": "f.peg_ratio",
    "dividend_yield": "f.dividend_yield",
    "debt_to_equity": "f.debt_to_equity",
    "sector": "s.sector",
    "company_name": "s.company_name",
    "ticker": "s.ticker"
}

# Fields that require special subquery handling
QUARTERLY_FIELDS = ["revenue", "net_profit", "ebitda"]

def compile_node(node: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    Recursively compiles a DSL node into a SQL fragment and parameters.
    Returns: (sql_string, list_of_parameters)
    """
    
    # CASE 1: GROUP NODE (Nested Logic)
    if "logic" in node and "filters" in node:
        logic = node["logic"].upper()
        if logic not in ["AND", "OR"]:
            raise ValueError(f"Invalid logic operator: {logic}")
        
        sub_sqls = []
        sub_params = []
        
        for child in node["filters"]:
            child_sql, child_params = compile_node(child)
            sub_sqls.append(child_sql)
            sub_params.extend(child_params)
            
        # Join with the logic operator and wrap in parentheses
        joined_sql = f"({f' {logic} '.join(sub_sqls)})"
        return joined_sql, sub_params

    # CASE 2: CONDITION NODE (Leaf Rule)
    elif "field" in node and "operator" in node:
        field = node["field"]
        op = node["operator"]
        value = node.get("value")
        
        # 2a. Handle Quarterly Logic (Complex Subquery)
        if field in QUARTERLY_FIELDS:
            # Note: Quarterly logic generates a full subquery string. 
            # Ideally, we'd parameterize inside that too, but for this specific 
            # hybrid integration, we assume the subquery string is safe/validated.
            n_quarters = node.get("quarters", 1)
            # We call your existing quarterly compiler
            subquery = compile_last_n_quarters_sql(field, op, value, n_quarters)
            return subquery, [] 

        # 2b. Handle Standard Logic
        db_column = FIELD_MAPPING.get(field)
        if not db_column:
            raise ValueError(f"Unknown field: {field}")
            
        if op == "between":
            # BETWEEN requires two values
            return f"{db_column} BETWEEN %s AND %s", [value[0], value[1]]
        
        elif op in ["=", "<", ">", "<=", ">="]:
            return f"{db_column} {op} %s", [value]
            
        else:
            raise ValueError(f"Unsupported operator: {op}")

    else:
        raise ValueError("Invalid DSL Node: Must be Group or Condition")

def compile_dsl_to_sql_with_params(dsl: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """Wrapper function to start compilation"""
    if not dsl:
        return "1=1", []
    return compile_node(dsl)
