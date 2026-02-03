import re

def parse_query_to_dsl(query: str):
    q = query.lower()

    # -------- QUARTERLY QUERY --------
    if "quarter" in q:
        num_match = re.search(r"(\d+)", q)
        n = int(num_match.group()) if num_match else 4

        if "profit" in q:
            return {
                "type": "quarterly",
                "metric": "net_profit",
                "operator": ">",
                "value": 0,
                "n": n
            }

        raise ValueError("Unsupported quarterly query")

    # -------- SNAPSHOT QUERY --------
    if "pe" in q:
        value = re.search(r"\d+", q)
        if not value:
            raise ValueError("PE value missing")

        return {
            "type": "snapshot",
            "conditions": [
                {"field": "pe_ratio", "operator": "<", "value": value.group()}
            ],
            "logic": "AND"
        }

    if "price" in q:
        value = re.search(r"\d+", q)
        if not value:
            raise ValueError("Price value missing")

        return {
            "type": "snapshot",
            "conditions": [
                {"field": "close_price", "operator": ">", "value": value.group()}
            ],
            "logic": "AND"
        }

    raise ValueError("Query not supported")
