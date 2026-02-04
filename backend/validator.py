def validate_dsl(node):
    if not isinstance(node, dict):
        raise ValueError("DSL node must be a dictionary")

    if "node" not in node:
        raise ValueError("DSL node missing 'node' key")

    # Condition node
    if node["node"] == "condition":
        required = ["field", "operator", "value"]
        for key in required:
            if key not in node:
                raise ValueError(f"Condition missing {key}")
        return True

    # Logical node
    if node["node"] == "logical":
        if node["op"] not in ("AND", "OR"):
            raise ValueError("Logical node must be AND or OR")

        validate_dsl(node["left"])
        validate_dsl(node["right"])
        return True

    raise ValueError("Unknown DSL node type")
