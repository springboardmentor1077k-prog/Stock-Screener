def build_last_n_quarters_subquery(metric, operator, value, n):
    return f"""
    m.stock_id IN (
        SELECT stock_id
        FROM (
            SELECT stock_id, {metric}
            FROM time_series_financials
            ORDER BY date DESC
        )
        WHERE {metric} {operator} {value}
        GROUP BY stock_id
        HAVING COUNT(*) >= {n}
    )
    """.strip()
