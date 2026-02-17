from rule_compile import compile_condition


def compile_dsl(node, allowed_fields=None, param_counter=[0]):

    params = {}

    # =================================================
    # LOGICAL GROUP
    # =================================================
    if "conditions" in node:

        logic = node.get("logic", "AND").upper()
        fragments = []

        for condition in node["conditions"]:
            sql_part, sub_params = compile_dsl(condition, allowed_fields, param_counter)
            fragments.append(f"({sql_part})")
            params.update(sub_params)

        joined = f" {logic} ".join(fragments)
        return joined, params

    # =================================================
    # QUARTERLY LOGIC
    # =================================================
    if "last_n_quarters" in node:

        n = int(node["last_n_quarters"])
        field = node["field"]
        operator = node["operator"]
        value = node["value"]
        count_required = int(node.get("count_required", n))

        param_name = f"param_{param_counter[0]}"
        param_counter[0] += 1
        params[param_name] = value

        sql = f"""
        EXISTS (
            SELECT 1
            FROM (
                SELECT q.company_id, q.{field}
                FROM quarterly_financials q
                WHERE q.company_id = c.company_id
                ORDER BY q.year DESC,
                CASE q.quarter
                    WHEN 'Q4' THEN 4
                    WHEN 'Q3' THEN 3
                    WHEN 'Q2' THEN 2
                    WHEN 'Q1' THEN 1
                END DESC
                LIMIT {n}
            ) latest_q
            WHERE latest_q.{field} {operator} :{param_name}
            GROUP BY latest_q.company_id
            HAVING COUNT(*) >= {count_required}
        )
        """

        return sql.strip(), params

    # =================================================
    # SIMPLE LEAF CONDITION → Delegate
    # =================================================
    return compile_condition(node, param_counter)
