"""
DSL to Database Field Mapper

This module maps DSL indicators and operators to database fields and SQLAlchemy operators.
"""

from typing import Dict, Any, List
from app.schemas.stock import FilterCondition

# =========================================================
# DSL INDICATOR TO DATABASE FIELD MAPPING
# =========================================================
DSL_TO_DB_FIELD_MAP = {
    # Valuation Metrics (Fundamentals table)
    "PE": "pe_ratio",
    "PB": "pb_ratio",
    "PS": "ps_ratio",
    "PEG": "peg_ratio",
    "MARKET_CAP": "market_cap",
    
    # Profitability Metrics (would need to be added to Fundamentals)
    "ROE": "roe",
    "ROA": "roa",
    "ROCE": "roce",
    
    # Financial Health (would need to be added to Fundamentals)
    "DEBT_EQUITY": "debt_to_equity",
    "CURRENT_RATIO": "current_ratio",
    "QUICK_RATIO": "quick_ratio",
    
    # Dividend (Fundamentals table)
    "DIVIDEND_YIELD": "div_yield",
    
    # Price/Volume (Fundamentals table)
    "PRICE": "current_price",
    "VOLUME": "volume",
    
    # Financial Statements (Financials table)
    "REVENUE": "revenue_generated",
    "EBITDA": "ebitda",
    "NET_PROFIT": "net_profit",
    "PROFIT": "net_profit",
    
    # Technical Indicators (not yet implemented in DB)
    "RSI": "rsi",
    "MACD": "macd",
    "ADX": "adx",
    "SMA": "sma",
    "EMA": "ema",
}

# =========================================================
# DSL OPERATOR TO SQLALCHEMY OPERATOR MAPPING
# =========================================================
DSL_TO_DB_OPERATOR_MAP = {
    ">": ">",
    "<": "<",
    ">=": ">=",
    "<=": "<=",
    "==": "==",
    "!=": "!=",
    "CROSS_ABOVE": "cross_above",  # Special handling needed
    "CROSS_BELOW": "cross_below",  # Special handling needed
}

# =========================================================
# FIELD TO MODEL MAPPING (for query building)
# =========================================================
FIELD_TO_MODEL = {
    # Fundamentals fields
    "pe_ratio": "Fundamentals",
    "pb_ratio": "Fundamentals",
    "ps_ratio": "Fundamentals",
    "peg_ratio": "Fundamentals",
    "market_cap": "Fundamentals",
    "div_yield": "Fundamentals",
    "current_price": "Fundamentals",
    "volume": "Fundamentals",
    "roe": "Fundamentals",
    "roa": "Fundamentals",
    "roce": "Fundamentals",
    "debt_to_equity": "Fundamentals",
    "current_ratio": "Fundamentals",
    "quick_ratio": "Fundamentals",
    
    # Financials fields
    "revenue_generated": "Financials",
    "ebitda": "Financials",
    "net_profit": "Financials",
    
    # Stock fields
    "symbol": "Stock",
    "company_name": "Stock",
    "sector": "Stock",
    "industry": "Stock",
}


def map_dsl_to_screener_query(dsl_result: Dict[str, Any]) -> List[FilterCondition]:
    """
    Convert DSL output to ScreenerQuery FilterCondition format.
    
    Args:
        dsl_result: Output from generate_dsl() function
        
    Returns:
        List of FilterCondition objects
        
    Raises:
        ValueError: If indicator or operator is not supported
    """
    if "error" in dsl_result:
        raise ValueError(f"DSL parsing error: {dsl_result['error']}")
    
    conditions = []
    
    for cond in dsl_result.get("conditions", []):
        left_indicator = cond["left"]["type"]
        operator = cond["operator"]
        right_value = cond["right"]
        
        # Map indicator to database field
        db_field = DSL_TO_DB_FIELD_MAP.get(left_indicator)
        if not db_field:
            raise ValueError(f"Unsupported indicator: {left_indicator}")
        
        # Map operator
        db_operator = DSL_TO_DB_OPERATOR_MAP.get(operator)
        if not db_operator:
            raise ValueError(f"Unsupported operator: {operator}")
        
        # Handle crossover operators (requires special logic)
        if operator in ["CROSS_ABOVE", "CROSS_BELOW"]:
            # For crossovers, right_value is another indicator
            if isinstance(right_value, dict) and "type" in right_value:
                right_indicator = right_value["type"]
                right_db_field = DSL_TO_DB_FIELD_MAP.get(right_indicator)
                if not right_db_field:
                    raise ValueError(f"Unsupported right indicator in crossover: {right_indicator}")
                
                # Store crossover as special condition
                conditions.append(FilterCondition(
                    field=db_field,
                    operator=db_operator,
                    value=right_db_field  # Store as string for special handling
                ))
            else:
                raise ValueError(f"Crossover operator requires two indicators")
        else:
            # Handle moving averages with periods
            if "period" in cond["left"]:
                # Store period information in field name (e.g., "sma_50")
                db_field = f"{db_field}_{cond['left']['period']}"
            
            # Regular numeric comparison
            conditions.append(FilterCondition(
                field=db_field,
                operator=db_operator,
                value=right_value
            ))
    
    return conditions


def get_model_for_field(field: str) -> str:
    """
    Get the model name for a given database field.
    
    Args:
        field: Database field name
        
    Returns:
        Model name (Stock, Fundamentals, or Financials)
    """
    # Handle fields with periods (e.g., sma_50)
    base_field = field.split('_')[0] + '_' + field.split('_')[1] if '_' in field and field.split('_')[0] in ['sma', 'ema'] else field
    
    return FIELD_TO_MODEL.get(field, FIELD_TO_MODEL.get(base_field, "Fundamentals"))
