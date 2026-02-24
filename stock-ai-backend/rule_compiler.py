from field_registry import FIELD_REGISTRY


def map_field_name(field):
    """
    Maps dotted field names (e.g., 'fundamentals.pe_ratio') to registry keys (e.g., 'pe_ratio').
    """
    # If field contains a dot, extract the actual field name
    if "." in field:
        return field.split(".")[-1]
    return field


def build_last_n_exists(node):
    """
    Builds an EXISTS subquery for last_n quarters.
    Example: Net profit > 0 for last 4 quarters
    """
    field_name = map_field_name(node["field"])
    meta = FIELD_REGISTRY[field_name]
    last_n = node["last_n"]
    operator = node["operator"]
    value = node["value"]

    # Build the EXISTS subquery
    # We need at least last_n matching records
    subquery = f"""
    (
        SELECT COUNT(*)
        FROM (
            SELECT 1
            FROM {meta['table']} q_inner
            WHERE q_inner.stock_id = s.id
            AND q_inner.{meta['column']} {operator} {value}
            ORDER BY q_inner.year DESC, q_inner.quarter DESC
            LIMIT {last_n}
        ) AS recent_quarters
    ) >= {last_n}
    """
    
    return subquery.strip()


def compile_node(node, params):
    """
    Recursively compiles a DSL node into SQL WHERE clause.
    """
    # CONDITION NODE
    if node["type"] == "condition":
        # Time-series with last_n
        if "last_n" in node:
            return build_last_n_exists(node)

        # Regular snapshot condition
        field_name = map_field_name(node["field"])
        meta = FIELD_REGISTRY[field_name]
        params.append(node["value"])
        return f"{meta['alias']}.{meta['column']} {node['operator']} %s"

    # LOGICAL NODE
    elif node["type"] == "logical":
        compiled = []
        # Support both 'children' and 'conditions' keys (same as validator)
        children = node.get("children") or node.get("conditions", [])
        for child in children:
            compiled.append(compile_node(child, params))
        joiner = f" {node['operator']} "
        return "(" + joiner.join(compiled) + ")"

    else:
        raise ValueError(f"Unknown node type: {node.get('type')}")


# Legacy function kept for backward compatibility
def compile_sql(dsl):
    """
    Old compile function - kept for backward compatibility.
    """
    joins = set()
    where = []

    for c in dsl["conditions"]:
        meta = FIELD_REGISTRY[c["field"]]
        alias = meta["alias"]
        column = meta["column"]
        table = meta["table"]
        op = c["operator"]
        val = c["value"]

        # joins
        if table == "fundamentals":
            joins.add("JOIN fundamentals f ON s.id = f.stock_id")

        elif table == "quarterly_financials":
            joins.add("JOIN quarterly_financials q ON s.id = q.stock_id")

        elif table == "analyst_targets":
            joins.add("JOIN analyst_targets a ON s.id = a.stock_id")

        # where clause
        if meta["type"] == "string":
            where.append(f"{alias}.{column} {op} '{val}'")
        else:
            where.append(f"{alias}.{column} {op} {val}")

    sql = f"""
    SELECT DISTINCT s.symbol, s.company_name
    FROM stocks_master s
    {' '.join(joins)}
    WHERE {' AND '.join(where)}
    """

    return sql
