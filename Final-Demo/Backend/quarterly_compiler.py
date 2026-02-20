def compile_last_n_quarters_sql(field: str, operator: str, value: float, n_quarters: int) -> str:
    """
    Generates a SQL subquery to find stock_ids where the condition matches 
    ALL of the last N quarters using Window Functions.
    Adapted for schema with 'year' and 'quarter' columns.
    """
    
    # Map DSL operators to SQL
    sql_op = operator
    if operator == "gt": sql_op = ">"
    elif operator == "lt": sql_op = "<"
    elif operator == "gte": sql_op = ">="
    elif operator == "lte": sql_op = "<="
    
    # Logic Explanation:
    # 1. Select latest N quarters per stock using ROW_NUMBER()
    #    SORT BY year DESC, quarter DESC (instead of date)
    # 2. Group by stock_id
    # 3. Ensure we have exactly N quarters of data (COUNT(*) = N)
    # 4. Ensure the condition matched for ALL those quarters (BOOL_AND)
    
    sql = f"""
    s.stock_id IN (
        SELECT stock_id 
        FROM (
            SELECT 
                stock_id, 
                {field},
                ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY year DESC, quarter DESC) as rn
            FROM quarterly_financials
        ) sub
        WHERE rn <= {n_quarters}
        GROUP BY stock_id
        HAVING COUNT(*) = {n_quarters} 
        AND BOOL_AND({field} {sql_op} {value})
    )
    """
    return sql