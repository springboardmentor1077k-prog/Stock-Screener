def validate_dsl(dsl):
    if not isinstance(dsl, dict):
        raise ValueError("DSL must be dict")

    if dsl.get("type") != "snapshot":
        raise ValueError("Only snapshot DSL supported")

    if "conditions" not in dsl:
        raise ValueError("Snapshot conditions missing")

    return True
