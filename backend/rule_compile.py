FIELD_MAPPING = {
    "pe_ratio": {
        "table": "fundamental_data",
        "column": "pe_ratio",
        "alias": "f"
    },
    "revenue": {
        "table": "fundamental_data",
        "column": "revenue",
        "alias": "f"
    },
    "debt": {
        "table": "fundamental_data",
        "column": "debt",
        "alias": "f"
    },
    "sector": {
        "table": "company_master",
        "column": "sector",
        "alias": "c"
    }
}


def compile_condition(condition, param_counter):
    """
    Compiles single non-nested condition.
    Returns: sql_fragment, params
    """

    field = condition["field"]
    operator = condition["operator"]
    value = condition["value"]

    if field not in FIELD_MAPPING:
        raise ValueError(f"Unsupported field: {field}")

    mapping = FIELD_MAPPING[field]
    column_ref = f"{mapping['alias']}.{mapping['column']}"

    param_name = f"param_{param_counter[0]}"
    param_counter[0] += 1

    params = {param_name: value}

    if operator in ["<", ">", "="]:
        return f"{column_ref} {operator} :{param_name}", params

    elif operator == "between":
        low, high = value
        return f"{column_ref} BETWEEN {low} AND {high}", {}

    else:
        raise ValueError(f"Unsupported operator: {operator}")
