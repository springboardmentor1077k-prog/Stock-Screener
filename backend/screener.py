from quarterly_compiler import build_last_n_quarters_subquery

def build_where_clause(dsl):
    # -------- SNAPSHOT --------
    if dsl["type"] == "snapshot":
        parts = []
        for cond in dsl["conditions"]:
            parts.append(
                f"{cond['field']} {cond['operator']} {cond['value']}"
            )
        return " AND " + " AND ".join(parts)

    # -------- QUARTERLY --------
    if dsl["type"] == "quarterly":
        return " AND " + build_last_n_quarters_subquery(
            metric=dsl["metric"],
            operator=dsl["operator"],
            value=dsl["value"],
            n=dsl["n"]
        )

    return ""
