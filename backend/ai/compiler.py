from backend.database import get_db

def compile_and_run(dsl):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    base_sql = """
    SELECT 
        s.symbol,
        s.company_name,
        s.sector,
        s.industry,
        s.exchange,
        f.pe_ratio,
        f.eps,
        f.market_cap,
        f.roe,
        f.debt_equity
    FROM stocks s
    JOIN fundamentals f ON s.stock_id = f.stock_id
    """

    where_clauses = []
    params = []

    for cond in dsl["conditions"]:

        # Snapshot PE ratio
        if cond["field"] == "pe_ratio":
            where_clauses.append(f"f.pe_ratio {cond['operator']} %s")
            params.append(cond["value"])

        # Quarterly net profit
        if cond.get("type") == "quarterly" and cond["field"] == "net_profit":
            where_clauses.append("""
            s.stock_id IN (
                SELECT q.stock_id
                FROM quarterly_finance q
                WHERE q.net_profit > 0
                GROUP BY q.stock_id
                HAVING COUNT(*) >= %s
            )
            """)
            params.append(cond["last_n"])

    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)

    cursor.execute(base_sql, params)
    results = cursor.fetchall()

    cursor.close()
    db.close()

    return results
