import re

FIELD_MAP = {
    "pe": "pe_ratio",
    "market cap": "market_cap",
    "profit": "profit",
    "net profit": "net_profit",
    "sector": "sector"
}

OPERATOR_MAP = {
    "below": "<",
    "less than": "<",
    "above": ">",
    "greater than": ">",
    "equals": "="
}

def parse_query_to_dsl(query: str):
    q = query.lower().strip()

    # -------------------------
    # QUARTERLY RULE (EXPLICIT)
    # net profit above 0 last 4 quarters
    # -------------------------
    m = re.match(
        r"(net profit|profit)\s+(above|below|equals)\s+(-?\d+)\s+last\s+(\d+)\s+quarters",
        q
    )

    if m:
        field_text, op_text, value, n = m.groups()
        return {
            "node": "quarterly",
            "field": FIELD_MAP[field_text],
            "operator": OPERATOR_MAP[op_text],
            "value": int(value),
            "n": int(n)
        }

    # -------------------------
    # OR
    # -------------------------
    if " or " in q:
        left, right = q.split(" or ", 1)
        return {
            "node": "logical",
            "op": "OR",
            "left": parse_query_to_dsl(left),
            "right": parse_query_to_dsl(right)
        }

    # -------------------------
    # AND
    # -------------------------
    if " and " in q:
        left, right = q.split(" and ", 1)
        return {
            "node": "logical",
            "op": "AND",
            "left": parse_query_to_dsl(left),
            "right": parse_query_to_dsl(right)
        }

    # -------------------------
    # SNAPSHOT CONDITION
    # -------------------------
    field = None
    for k in FIELD_MAP:
        if k in q:
            field = FIELD_MAP[k]
            break

    if not field:
        raise ValueError("Unsupported field")

    operator = None
    for k in OPERATOR_MAP:
        if k in q:
            operator = OPERATOR_MAP[k]
            break

    if not operator:
        raise ValueError("Unsupported operator")

    value_match = re.search(r"-?\d+", q)
    value = int(value_match.group()) if value_match else q.split()[-1].upper()

    return {
        "node": "condition",
        "field": field,
        "operator": operator,
        "value": value
    }

