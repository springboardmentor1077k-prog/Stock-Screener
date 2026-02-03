def build_where_clause(dsl):
    conditions = dsl["conditions"]
    logic = dsl["logic"]

    sql_parts = []

    for cond in conditions:
        field = cond["field"]
        operator = cond["operator"]
        value = cond["value"]

        sql_parts.append(f"{field} {operator} {value}")

    # ❗ NO "WHERE" HERE
    return " AND " + f" {logic} ".join(sql_parts)

