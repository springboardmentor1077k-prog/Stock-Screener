import re

def parse_query_to_dsl(query: str):
    q = query.lower()

    # SNAPSHOT: PE
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

    # SNAPSHOT: PRICE
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

    raise ValueError("Only snapshot queries supported right now")

