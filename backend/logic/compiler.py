def compile_sql(dsl_json):
    """Compile DSL JSON filters into a parameterized SQL query."""
    base_query = """SELECT symbol, company_name, sector, sub_sector, price, change_pct, pe_ratio, 
                    market_cap, promoter_holding, has_buyback, revenue_growth,
                    q1_earnings, q2_earnings, q3_earnings, q4_earnings,
                    eps, dividend_yield, debt_to_equity, roe, exchange,
                    peg_ratio, earnings_growth_rate, free_cash_flow, total_debt, debt_to_fcf,
                    analyst_price_low, analyst_price_high, analyst_price_avg, price_vs_target,
                    revenue_growth_yoy, ebitda, ebitda_growth_yoy,
                    estimated_eps, historical_beat_rate, likely_to_beat,
                    next_earnings_date, earnings_within_30_days
                    FROM stocks"""
    filters = dsl_json.get("filters", [])
    
    if not filters:
        return base_query + " ORDER BY market_cap DESC LIMIT 100", []

    where_clauses = []
    params = []
    
    for f in filters:
        field = f.get('field', '')
        op = f.get('op', '=')
        value = f.get('value')
        
        # Validate field name (prevent SQL injection)
        allowed_fields = [
            'symbol', 'company_name', 'sector', 'sub_sector', 'price', 'change_pct', 
            'pe_ratio', 'market_cap', 'promoter_holding', 'has_buyback', 
            'revenue_growth', 'q1_earnings', 'q2_earnings', 'q3_earnings', 
            'q4_earnings', 'eps', 'dividend_yield', 'debt_to_equity', 
            'roe', 'exchange',
            # New fields
            'peg_ratio', 'earnings_growth_rate', 'free_cash_flow', 'total_debt', 'debt_to_fcf',
            'analyst_price_low', 'analyst_price_high', 'analyst_price_avg', 'price_vs_target',
            'revenue_growth_yoy', 'ebitda', 'ebitda_growth_yoy',
            'estimated_eps', 'historical_beat_rate', 'likely_to_beat',
            'next_earnings_date', 'earnings_within_30_days'
        ]
        
        if field not in allowed_fields:
            continue
        
        # Normalize operator
        if op == '==':
            op = '='
        
        # Handle IN operator for arrays
        if op == 'IN' and isinstance(value, list):
            placeholders = ', '.join(['%s'] * len(value))
            where_clauses.append(f"{field} IN ({placeholders})")
            params.extend(value)
            continue
        
        # Validate operator
        if op not in ['<', '>', '<=', '>=', '=', '!=']:
            continue
        
        where_clauses.append(f"{field} {op} %s")
        params.append(value)
    
    if where_clauses:
        sql = f"{base_query} WHERE {' AND '.join(where_clauses)} ORDER BY market_cap DESC LIMIT 100"
    else:
        sql = base_query + " ORDER BY market_cap DESC LIMIT 100"
    
    return sql, params