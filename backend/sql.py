def build_where_clauses(dsl, allowed_fields):

    where_clauses = []
    conditions = dsl.get("conditions", [])
    logic = dsl.get("logic", "AND").upper()

    for cond in conditions:

        # =================================================
        # QUARTERLY LOGIC (GROUP BY + HAVING + COUNT)
        # =================================================
        if "last_n_quarters" in cond:

            n = int(cond["last_n_quarters"])
            field = cond["field"]
            operator = cond["operator"]
            value = cond["value"]

            # Optional: count_required support
            count_required = int(cond.get("count_required", n))

            if field not in ["profit", "revenue"]:
                raise ValueError(f"Unsupported quarterly field: {field}")

            subquery = f"""
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
                WHERE latest_q.{field} {operator} {value}
                GROUP BY latest_q.company_id
                HAVING COUNT(*) >= {count_required}
            )
            """

            where_clauses.append(subquery)
            continue

        # =================================================
        # FUNDAMENTAL LOGIC
        # =================================================
        field = cond.get("field")
        operator = cond.get("operator")
        value = cond.get("value")

        if field not in allowed_fields:
            raise ValueError(f"Unsupported field: {field}")

        db_column = allowed_fields[field]

        if field == "sector":
            clause = f"{db_column} {operator} '{value}'"
        else:
            value = float(value)
            clause = f"{db_column} {operator} {value}"

        where_clauses.append(clause)

    return where_clauses, logic
