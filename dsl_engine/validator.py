from typing import Any, Dict, Tuple, List

SUPPORTED_FIELDS: List[str] = [
    "industry_category",
    "peg_ratio_max",
    "fcf_to_debt_min",
    "price_vs_target",
    "revenue_yoy_positive",
    "ebitda_yoy_positive",
    "earnings_beat_likely",
    "buyback_announced",
    "next_earnings_within_days",
]

SUPPORTED_OPERATORS = {"AND", "OR"}

def validate_dsl(dsl: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates a DSL dict structure and values.
    Returns (is_valid, error_message). error_message is empty when valid.
    """
    if not isinstance(dsl, dict):
        return False, "DSL must be an object"

    if "query" not in dsl:
        return False, "Missing required field: query"

    # Optional time series/limit
    if "last_n_quarters" in dsl:
        n = dsl["last_n_quarters"]
        if not isinstance(n, int) or n <= 0:
            return False, "Invalid last_n_quarters: must be positive integer"

    # Validate query node recursively
    def validate_node(node: Dict[str, Any]) -> Tuple[bool, str]:
        if not isinstance(node, dict) or "type" not in node:
            return False, "Malformed DSL node: missing type"
        node_type = node["type"]
        if node_type == "condition":
            if "field" not in node or "value" not in node:
                return False, "Condition missing required fields"
            field = node["field"]
            if field not in SUPPORTED_FIELDS:
                return False, f"Unsupported field: {field}"
            # Simple value validations
            if field == "price_vs_target":
                if node["value"] not in ("<= target_low", "<= target_mean"):
                    return False, "Wrong operator for price_vs_target"
            if field == "next_earnings_within_days":
                if not isinstance(node["value"], int) or node["value"] < 0:
                    return False, "Invalid value for next_earnings_within_days"
            return True, ""
        elif node_type == "logical":
            op = node.get("operator")
            if op not in SUPPORTED_OPERATORS:
                return False, f"Wrong operator: {op}"
            children = node.get("children", [])
            if not isinstance(children, list) or len(children) == 0:
                return False, "Logical node must have children"
            for child in children:
                ok, msg = validate_node(child)
                if not ok:
                    return False, msg
            return True, ""
        else:
            return False, f"Unsupported node type: {node_type}"

    ok, msg = validate_node(dsl["query"])
    if not ok:
        return False, msg
    return True, ""
