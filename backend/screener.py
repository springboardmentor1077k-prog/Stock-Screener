def compile_node(node):
    # Condition node
    if node["node"] == "condition":
        value = node["value"]
        if isinstance(value, str):
            value = f"'{value}'"

        return f"{node['field']} {node['operator']} {value}"

    # Logical node
    if node["node"] == "logical":
        left_sql = compile_node(node["left"])
        right_sql = compile_node(node["right"])
        return f"({left_sql} {node['op']} {right_sql})"

    raise ValueError("Invalid DSL node")


def build_where_clause(dsl):
    return " AND " + compile_node(dsl)

