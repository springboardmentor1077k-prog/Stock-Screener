ALLOWED_FIELDS = {"pe_ratio", "peg_ratio", "sector"}
ALLOWED_OPERATORS = {"=", "<", "between"}
ALLOWED_LOGIC = {"AND", "OR"}

def validate_dsl(dsl: dict):
    if "filters" not in dsl or "logic" not in dsl:
        raise ValueError("Invalid DSL structure")

    if dsl["logic"] not in ALLOWED_LOGIC:
        raise ValueError("Invalid logic operator")

    for f in dsl["filters"]:
        if f["field"] not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field {f['field']}")

        if f["operator"] not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator {f['operator']}")