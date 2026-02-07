from quarterly_compiler import build_last_n_quarters_subquery

def compile_node(node):
    # -------------------------
    # SNAPSHOT CONDITION
    # -------------------------
    if node["node"] == "condition":
        val = node["value"]
        if isinstance(val, str):
            val = f"'{val}'"
        return f"{node['field']} {node['operator']} {val}"

    # -------------------------
    # LOGICAL
    # -------------------------
    if node["node"] == "logical":
        left = compile_node(node["left"])
        right = compile_node(node["right"])
        return f"({left} {node['op']} {right})"

    # -------------------------
    # QUARTERLY
    # -------------------------
    if node["node"] == "quarterly":
        return build_last_n_quarters_subquery(
            metric=node["field"],
            operator=node["operator"],
            value=node["value"],
            n=node["n"]
        )

    raise ValueError("Invalid DSL node")

def build_where_clause(dsl):
    return " AND " + compile_node(dsl)
