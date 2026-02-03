def build_last_n_quarters_subquery(metric, operator, value, n):
    """
    Ensure the metric satisfies condition
    for the last N quarters for each stock
    """

    return f"""
    m.stock_id IN (
        SELECT ts.stock_id
        FROM (
            SELECT stock_id, date, {metric}
            FROM time_series_financials
            ORDER BY date DESC
        ) ts
        WHERE ts.{metric} {operator} {value}
        GROUP BY ts.stock_id
        HAVING COUNT(*) >= {n}
    )
    """.strip()

