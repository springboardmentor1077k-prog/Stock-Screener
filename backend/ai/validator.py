ALLOWED_FIELDS = {"pe_ratio", "net_profit"}
ALLOWED_OPERATORS = {">", ">=", "<", "<=", "="}
ALLOWED_QUARTERLY_CONDITIONS = {"positive", "negative"}

def validate_dsl(dsl: dict):
    """Strictly validate DSL structure and content."""
    if not isinstance(dsl, dict):
        raise ValueError("DSL must be a dictionary")
        
    if "conditions" not in dsl:
        raise ValueError("Missing 'conditions' field")
        
    if not isinstance(dsl["conditions"], list):
        raise ValueError("'conditions' must be a list")
        
    if len(dsl["conditions"]) == 0:
        raise ValueError("At least one condition is required")

    for i, cond in enumerate(dsl["conditions"]):
        if not isinstance(cond, dict):
            raise ValueError(f"Condition {i} must be a dictionary")
            
        field = cond.get("field")
        if not field:
            raise ValueError(f"Condition {i} missing 'field'")
            
        if field not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field '{field}'. Allowed fields: {', '.join(ALLOWED_FIELDS)}")

        if "operator" in cond:
            operator = cond.get("operator")
            if operator not in ALLOWED_OPERATORS:
                raise ValueError(f"Invalid operator '{operator}'. Allowed: {', '.join(ALLOWED_OPERATORS)}")
                
            value = cond.get("value")
            if not isinstance(value, (int, float)):
                raise ValueError(f"Condition {i} value must be a number")
                
            if value < 0:
                raise ValueError(f"Condition {i} value must be non-negative")

        elif cond.get("type") == "quarterly":
            if field != "net_profit":
                raise ValueError("Quarterly conditions only supported for net_profit")
                
            condition = cond.get("condition")
            if condition not in ALLOWED_QUARTERLY_CONDITIONS:
                raise ValueError(f"Invalid quarterly condition '{condition}'. Allowed: {', '.join(ALLOWED_QUARTERLY_CONDITIONS)}")
                
            last_n = cond.get("last_n")
            if not isinstance(last_n, int) or last_n <= 0:
                raise ValueError("'last_n' must be a positive integer")
                
            if last_n > 20:
                raise ValueError("'last_n' cannot exceed 20 quarters")
        else:
            raise ValueError(f"Condition {i} must have either 'operator' or 'type': 'quarterly'")
    
    logic = dsl.get("logic", "AND")
    if logic not in ["AND", "OR"]:
        raise ValueError("Logic must be 'AND' or 'OR'")
        
    return True
