def validate_dsl(dsl):
    if not isinstance(dsl, dict):
        raise ValueError("DSL must be dict")

    if "type" not in dsl:
        raise ValueError("DSL missing type")

    if dsl["type"] == "snapshot":
        if "conditions" not in dsl:
            raise ValueError("Snapshot conditions missing")

    elif dsl["type"] == "quarterly":
        required = ["metric", "operator", "value", "n"]
        for key in required:
            if key not in dsl:
                raise ValueError(f"Quarterly DSL missing {key}")

    else:
        raise ValueError("Unsupported DSL type")

    return True
