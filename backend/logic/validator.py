import re

def is_safe_query(sql_query: str):
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE"]
    query_upper = sql_query.upper()
    for word in forbidden:
        if re.search(r'\b' + word + r'\b', query_upper):
            return False, f"Security Risk: {word} detected"
    if not query_upper.strip().startswith("SELECT"):
        return False, "Only SELECT allowed"
    return True, "Safe"