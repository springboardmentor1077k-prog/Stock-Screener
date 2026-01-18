import json
import re
import sys

# --------------------------------
# FIELD DEFINITIONS
# --------------------------------

FIELD_MAP = {
    "pe ratio": "pe_ratio",
    "price to book": "pb_ratio",
    "debt to equity": "de_ratio",
    "eps": "eps",
    "roe": "roe",
    "promoter holding": "promoter_holding"
}

ALLOWED_OPERATORS = {"<", ">"}

# --------------------------------
# INPUT PARSER (LLM SIMULATION)
# --------------------------------

def call_llm(user_query):
    query = user_query.lower().strip()

    # Reject unknown characters
    if not re.fullmatch(r"[a-z0-9 <>\sand]+", query):
        return json.dumps({"error": "unknown characters in input"})

    filters = []

    for text, field in FIELD_MAP.items():
        # Match patterns like: pe ratio < 10
        pattern = rf"{text}\s*(<|>)\s*(\d+)"
        match = re.search(pattern, query)

        if match:
            operator = match.group(1)
            value = int(match.group(2))

            filters.append({
                "field": field,
                "operator": operator,
                "value": value
            })

    if not filters:
        return json.dumps({"error": "no supported metrics found"})

    dsl = {"filters": filters}

    # Add logic ONLY if multiple filters
    if len(filters) > 1:
        dsl["logic"] = "and"

    return json.dumps(dsl)

# --------------------------------
# STEP 1: SCHEMA VALIDATION
# --------------------------------

def schema_validation(dsl):
    if "filters" not in dsl or not isinstance(dsl["filters"], list):
        raise ValueError("Invalid schema: filters missing")

    for f in dsl["filters"]:
        if not isinstance(f["field"], str):
            raise ValueError("Field must be string")
        if not isinstance(f["operator"], str):
            raise ValueError("Operator must be string")
        if not isinstance(f["value"], int):
            raise ValueError("Value must be number")

# --------------------------------
# STEP 2: WHITELIST VALIDATION
# --------------------------------

def whitelist_validation(dsl):
    for f in dsl["filters"]:
        if f["field"] not in FIELD_MAP.values():
            raise ValueError(f"Field not allowed: {f['field']}")
        if f["operator"] not in ALLOWED_OPERATORS:
            raise ValueError(f"Operator not allowed: {f['operator']}")

# --------------------------------
# STEP 3: BUSINESS RULE VALIDATION
# --------------------------------

def business_rules_validation(dsl):
    for f in dsl["filters"]:
        if f["value"] <= 0:
            raise ValueError("Metric values must be positive")

# --------------------------------
# VALIDATION SERVICE
# --------------------------------

def validate_dsl(dsl):
    schema_validation(dsl)
    whitelist_validation(dsl)
    business_rules_validation(dsl)

# --------------------------------
# MAIN BACKEND FLOW
# --------------------------------

def main():
    user_query = input("Enter your stock screening query: ")

    llm_response = call_llm(user_query)

    try:
        dsl = json.loads(llm_response)
    except json.JSONDecodeError:
        print("❌ ERROR: Invalid JSON")
        sys.exit(1)

    if "error" in dsl:
        print("❌ INPUT ERROR:", dsl["error"])
        sys.exit(1)

    try:
        validate_dsl(dsl)
    except ValueError as err:
        print("❌ VALIDATION ERROR:", err)
        sys.exit(1)

    print("\n✅ QUERY VALIDATED SUCCESSFULLY")
    print(json.dumps(dsl, indent=2))

# --------------------------------
# RUN
# --------------------------------

if __name__ == "__main__":
    main()
