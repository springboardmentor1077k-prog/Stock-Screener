def compile_query(conditions, logic):
    sql_fragments = []
    parameters = {}

    for idx, condition in enumerate(conditions):
        param_name = f"value_{idx}"

        sql_fragments.append(
            f"f.{condition.field} {condition.operator} :{param_name}"
        )

        parameters[param_name] = condition.value

    where_clause = f" {logic} ".join(sql_fragments)

    final_query = f"""
        SELECT s.symbol, s.name, f.pe_ratio, f.peg_ratio, f.promoter_holding
        FROM stocks s
        JOIN fundamentals f ON s.id = f.stock_id
        WHERE {where_clause}
        LIMIT 100
    """

    return final_query, parameters