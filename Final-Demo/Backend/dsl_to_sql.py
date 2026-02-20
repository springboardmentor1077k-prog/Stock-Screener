def dsl_to_sql(dsl: dict):
    conditions = []

    for f in dsl["filters"]:
        field = f["field"]
        op = f["operator"]
        value = f["value"]

        if op == "=":
            conditions.append(f"{field} = '{value}'")

        elif op == "<":
            conditions.append(f"{field} < {value}")

        elif op == "between":
            conditions.append(
                f"{field} BETWEEN {value[0]} AND {value[1]}"
            )

    joiner = f" {dsl['logic']} "
    return joiner.join(conditions) 