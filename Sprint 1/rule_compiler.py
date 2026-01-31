from typing import Dict, Any
import logging
from quarterly_compiler import compile_last_n_quarters_sql  # ✅ Import the new compiler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompilationError(Exception):
    """Raised when DSL compilation fails"""
    pass


# ✅ Define which fields require the quarterly logic
QUARTERLY_FIELDS = ["revenue", "net_profit", "ebitda"]


def compile_rule(condition: Dict[str, Any]) -> str:
    """Compile a single DSL rule to SQL fragment"""
    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")
    
    if not field or not operator:
        raise CompilationError("Invalid condition: missing field or operator")
    
    # ---------------------------------------------------------
    # 1. NEW: Quarterly Logic Routing
    # ---------------------------------------------------------
    if field in QUARTERLY_FIELDS:
        # Extract 'quarters' param, default to 1 if not provided
        n_quarters = condition.get("quarters", 1)
        logger.info(f"Compiling quarterly logic for {field} (Last {n_quarters} Qs)")
        return compile_last_n_quarters_sql(field, operator, value, n_quarters)

    # ---------------------------------------------------------
    # 2. Standard Logic (with Table Aliases)
    # ---------------------------------------------------------
    # Determine table alias: 's' for stocks table, 'f' for fundamentals
    prefix = "s" if field in ["sector", "company_name", "ticker"] else "f"
    column = f"{prefix}.{field}"

    # Type-safe value handling
    if operator == "between":
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return f"{column} BETWEEN {value[0]} AND {value[1]}"
            
    elif operator == "=":
        if isinstance(value, str):
            return f"{column} = '{value}'"
        else:
            return f"{column} = {value}"
            
    elif operator in ("<", ">", "<=", ">=", "!="):
        return f"{column} {operator} {value}"
    
    raise CompilationError(f"Unsupported operator: {operator}")


def compile_dsl_to_sql(dsl: Dict[str, Any]) -> str:
    """Compile DSL to SQL WHERE clause with AND/OR support."""
    try:
        # Handle compound AND conditions
        if "and" in dsl:
            logger.info(f"Compiling compound AND with {len(dsl['and'])} conditions")
            conditions = dsl["and"]
            compiled = [compile_rule(c) for c in conditions]
            result = " AND ".join(compiled)
            logger.info(f"Final SQL WHERE: {result}")
            return result
        
        # Handle compound OR conditions
        if "or" in dsl:
            logger.info(f"Compiling compound OR with {len(dsl['or'])} conditions")
            conditions = dsl["or"]
            compiled = [compile_rule(c) for c in conditions]
            return " OR ".join(compiled)
        
        # Handle single condition
        return compile_rule(dsl)
        
    except Exception as e:
        raise CompilationError(f"Failed to compile DSL to SQL: {str(e)}")