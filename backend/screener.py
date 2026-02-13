from quarterly_compiler import build_last_n_quarters_subquery

def compile_condition(node):
    field = node["field"]
    operator = node["operator"]
    value = node["value"]

    # Quote string values
    if isinstance(value, str):
        value_sql = f"'{value}'"
    else:
        value_sql = value

    # Quarterly logic ONLY when explicitly present
    if node.get("timeframe") == "quarters":
        return build_last_n_quarters_subquery(
            metric=field,
            operator=operator,
            value=value_sql,
            n=node["period"]
        )

    # Snapshot condition ONLY
    return f"{field} {operator} {value_sql}"


def compile_node(node):
    if node["node"] == "condition":
        return compile_condition(node)

    if node["node"] == "logical":
        left_sql = compile_node(node["left"])
        right_sql = compile_node(node["right"])
        return f"({left_sql} {node['op']} {right_sql})"

    raise ValueError("Invalid DSL node")


def build_where_clause(dsl):
    compiled = compile_node(dsl)
    return f" AND {compiled}"
