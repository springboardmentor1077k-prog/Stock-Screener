def validate_dsl(node):
    if node["node"] == "condition":
        return True

    if node["node"] == "logical":
        validate_dsl(node["left"])
        validate_dsl(node["right"])
        return True

    if node["node"] == "quarterly":
        return True

    raise ValueError("Invalid DSL node")
