def build_last_n_quarters_subquery(metric, operator, value, n):
    """
    Builds SQL EXISTS subquery for:
    metric operator value
    applied to LAST N QUARTERS
    """

    subquery = f"""
    EXISTS (
        SELECT 1
        FROM (
            SELECT stock_id
            FROM time_series_financials
            WHERE {metric} {operator} {value}
            ORDER BY date DESC
            LIMIT {n}
        ) recent
        GROUP BY stock_id
        HAVING COUNT(*) = {n}
    )
    """

    return subquery.strip()
