import re

# -------------------------
# FIELD MAP
# -------------------------
FIELD_MAP = {
    "pe": "pe_ratio",
    "p/e": "pe_ratio",
    "market cap": "market_cap",
    "marketcap": "market_cap",
    "sector": "sector",
    "profit": "profit",
    "net profit": "net_profit",
    "price": "close_price"
}

# -------------------------
# OPERATOR MAP
# -------------------------
OPERATOR_MAP = {
    "<=": "<=",
    ">=": ">=",
    "<": "<",
    ">": ">",
    "less than": "<",
    "below": "<",
    "greater than": ">",
    "above": ">",
    "equals": "=",
    "equal to": "="
}

# -------------------------
# NORMALIZATION
# -------------------------
def normalize_query(q: str) -> str:
    q = q.lower()

    replacements = {
        "<=": " less than or equal ",
        ">=": " greater than or equal ",
        "<": " less than ",
        ">": " greater than "
    }

    for k, v in replacements.items():
        q = q.replace(k, v)

    q = re.sub(r"\s+", " ", q)
    return q.strip()

# -------------------------
# PARSE CONDITION
# -------------------------
def parse_single_condition(text):
    field = None
    for k in FIELD_MAP:
        if k in text:
            field = FIELD_MAP[k]
            break

    if not field:
        raise ValueError("Unsupported field")

    operator = None
    for k in OPERATOR_MAP:
        if k in text:
            operator = OPERATOR_MAP[k]
            break

    if not operator:
        raise ValueError("Unsupported operator")

    value_match = re.search(r"-?\d+(\.\d+)?", text)
    if value_match:
        value = float(value_match.group())
    else:
        value = text.split()[-1].upper()

    return {
        "node": "condition",
        "field": field,
        "operator": operator,
        "value": value
    }

# -------------------------
# PARSE QUERY TO DSL
# -------------------------
def parse_query_to_dsl(query: str):
    q = normalize_query(query)

    if " or " in q:
        left, right = q.split(" or ", 1)
        return {
            "node": "logical",
            "op": "OR",
            "left": parse_query_to_dsl(left),
            "right": parse_query_to_dsl(right)
        }

    if " and " in q:
        left, right = q.split(" and ", 1)
        return {
            "node": "logical",
            "op": "AND",
            "left": parse_query_to_dsl(left),
            "right": parse_query_to_dsl(right)
        }

    return parse_single_condition(q)
