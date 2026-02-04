import re

# -------------------------
# FIELD & OPERATOR MAP
# -------------------------
FIELD_MAP = {
    "pe": "pe_ratio",
    "price": "close_price",
    "profit": "profit",
    "market cap": "market_cap",
    "sector": "sector"
}

OPERATOR_MAP = {
    "below": "<",
    "less than": "<",
    "above": ">",
    "greater than": ">",
    "equals": "="
}


def parse_single_condition(text):
    text = text.strip().lower()

    field = None
    for key in FIELD_MAP:
        if key in text:
            field = FIELD_MAP[key]
            break

    if not field:
        raise ValueError("Unsupported field")

    operator = None
    for key in OPERATOR_MAP:
        if key in text:
            operator = OPERATOR_MAP[key]
            break

    if not operator:
        raise ValueError("Unsupported operator")

    value_match = re.search(r"\d+", text)
    if value_match:
        value = int(value_match.group())
    else:
        # string value (e.g. sector IT)
        parts = text.split()
        value = parts[-1].upper()

    return {
        "node": "condition",
        "field": field,
        "operator": operator,
        "value": value
    }


def parse_query_to_dsl(query: str):
    q = query.lower()

    # OR has lowest precedence
    if " or " in q:
        left, right = q.split(" or ", 1)
        return {
            "node": "logical",
            "op": "OR",
            "left": parse_query_to_dsl(left),
            "right": parse_query_to_dsl(right)
        }

    # AND
    if " and " in q:
        left, right = q.split(" and ", 1)
        return {
            "node": "logical",
            "op": "AND",
            "left": parse_query_to_dsl(left),
            "right": parse_query_to_dsl(right)
        }

    # Base condition
    return parse_single_condition(q)
