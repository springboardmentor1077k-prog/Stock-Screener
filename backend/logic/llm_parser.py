import json
import re


def parse_to_dsl(user_query: str):
    """
    Parses natural language stock queries into structured DSL.
    Uses rule-based parsing for reliability (no external API dependency).
    Supports complex queries with multiple conditions.
    
    Supported criteria:
    - Sector/Sub-sector (IT, Semiconductor, Software, etc.)
    - PEG ratio
    - Debt to FCF ratio
    - Price vs analyst targets
    - Revenue & EBITDA growth Y-o-Y
    - Likely to beat earnings
    - Has buyback
    - Earnings within 30 days
    - PE ratio, promoter holding, ROE, EPS, etc.
    """
    query_lower = user_query.lower()
    filters = []
    
    # Parse exchange (NSE/BSE)
    if 'nse' in query_lower:
        filters.append({"field": "exchange", "op": "=", "value": "NSE"})
    elif 'bse' in query_lower:
        filters.append({"field": "exchange", "op": "=", "value": "BSE"})
    
    # Parse IT sub-sectors (more specific before general)
    sub_sectors = {
        r'\bsemiconductor\b': 'Semiconductor',
        r'\bchip\s*(?:maker)?s?\b': 'Semiconductor',
        r'\benterprise\s+software\b': 'Enterprise Software',
        r'\bcloud\s*(?:computing)?\b': 'Cloud Computing',
        r'\bhardware\b': 'Computer Hardware',
        r'\bcomputer\s+hardware\b': 'Computer Hardware',
        r'\btelecom\s*(?:equipment)?\b': 'Telecom Equipment',
        r'\btelecommunication\b': 'Telecom Equipment',
        r'\bcybersecurity\b': 'Cybersecurity',
        r'\bsecurity\s+(?:software|solutions)\b': 'Cybersecurity',
        r'\bdata\s*center\b': 'Data Center & Infrastructure',
        r'\binfrastructure\b': 'Data Center & Infrastructure',
        r'\b(?:ai|artificial\s+intelligence)\b': 'AI & Machine Learning',
        r'\bmachine\s+learning\b': 'AI & Machine Learning',
        r'\bfintech\b': 'Fintech & Payments',
        r'\bpayment\s*(?:processing)?\b': 'Fintech & Payments',
        r'\bnetworking\b': 'Networking & Communications',
        r'\bgaming\b': 'Gaming & Interactive',
        r'\binternet\s+services?\b': 'Internet Services',
        r'\bsoftware\b': 'Enterprise Software',
    }
    
    for pattern, sub_sector in sub_sectors.items():
        if re.search(pattern, query_lower):
            filters.append({"field": "sub_sector", "op": "=", "value": sub_sector})
            break
    
    # Parse sector (use word boundaries to avoid false positives)
    # Now primarily Information Technology focused
    sectors = {
        r'\binformation\s+technology\b': 'Information Technology',
        r'\bit\s+(?:sector|stocks?|companies?)': 'Information Technology',
        r'\btechnology\b': 'Information Technology', 
        r'\btech\b': 'Information Technology',
    }
    
    # Only add sector if no sub-sector was found
    sector_found = any(f["field"] == "sub_sector" for f in filters)
    if not sector_found:
        for pattern, sector in sectors.items():
            if re.search(pattern, query_lower):
                filters.append({"field": "sector", "op": "=", "value": sector})
                break
    
    # ========== NEW CRITERIA ==========
    
    # Parse PEG ratio conditions
    peg_patterns = [
        (r'peg\s*(?:ratio)?\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'peg\s*(?:ratio)?\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'peg\s*(?:ratio)?\s*<=\s*(\d+(?:\.\d+)?)', '<='),
        (r'peg\s*(?:ratio)?\s*>=\s*(\d+(?:\.\d+)?)', '>='),
        (r'peg\s*(?:ratio)?\s*(?:less\s+than|under|below)\s*(\d+(?:\.\d+)?)', '<'),
        (r'peg\s*(?:ratio)?\s*(?:greater\s+than|above|over)\s*(\d+(?:\.\d+)?)', '>'),
        (r'low\s+peg', '<'),  # Default to < 2
    ]
    
    for pattern, op in peg_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex else 2
                filters.append({"field": "peg_ratio", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse debt to FCF ratio (can repay debt in X years)
    debt_fcf_patterns = [
        (r'debt\s*(?:to\s*)?(?:fcf|free\s*cash\s*flow)\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'debt\s*(?:to\s*)?(?:fcf|free\s*cash\s*flow)\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'debt\s*(?:to\s*)?(?:fcf|free\s*cash\s*flow)\s*(?:ratio)?\s*(?:less\s+than|under|below)\s*(\d+(?:\.\d+)?)', '<'),
        (r'(?:can\s+)?repay\s+(?:their\s+)?debt\s+in\s+(\d+)\s+years?\s+or\s+less', '<='),
        (r'debt\s+repayable\s+in\s+(\d+)\s+years?', '<='),
        (r'minimum\s+debt\s+to\s+(?:free\s+)?cash\s+flow\s+(?:ratio\s+)?(?:of\s+)?(?:0\.)?(\d+)', '<='),
    ]
    
    for pattern, op in debt_fcf_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex else 4
                # If percentage like 0.25 or 25%, convert to years
                if value < 1:
                    value = 1 / value  # 0.25 = 4 years
                elif value >= 25 and value <= 100:
                    value = 100 / value  # 25% = 4 years
                filters.append({"field": "debt_to_fcf", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse price vs analyst target
    price_target_patterns = [
        (r'(?:price\s+)?(?:below|under)\s+(?:analyst\s+)?(?:price\s+)?(?:target|low)', '=', "Below Low"),
        (r'(?:price\s+)?(?:near|close\s+to)\s+(?:the\s+)?(?:low|lower)\s+(?:end|target)', '=', "Near Low"),
        (r'(?:price\s+)?(?:closer\s+to\s+(?:the\s+)?low)', 'IN', ["Below Low", "Near Low"]),
        (r'(?:below|under)\s+analyst\s+(?:price\s+)?target', 'IN', ["Below Low", "Near Low"]),
    ]
    
    for pattern, op, value in price_target_patterns:
        if re.search(pattern, query_lower):
            if op == 'IN':
                filters.append({"field": "price_vs_target", "op": "IN", "value": value})
            else:
                filters.append({"field": "price_vs_target", "op": op, "value": value})
            break
    
    # Parse revenue growth Y-o-Y
    revenue_yoy_patterns = [
        (r'revenue[s]?\s*(?:and\s+ebitda\s+)?(?:are\s+)?growing\s*(?:y[_-]?o[_-]?y)?', '>', 0),
        (r'revenue[s]?\s+(?:growth\s+)?(?:y[_-]?o[_-]?y|year\s*(?:over|on)\s*year)\s*[>]\s*(\d+(?:\.\d+)?)', '>', None),
        (r'positive\s+revenue\s+growth', '>', 0),
        (r'revenue[s]?\s+(?:not\s+)?shrinking', '>', 0),
        (r'growing\s+revenue[s]?', '>', 0),
    ]
    
    for pattern, op, default in revenue_yoy_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex and match.group(1) else default
                if value is None:
                    value = 0
                filters.append({"field": "revenue_growth_yoy", "op": op, "value": value})
            except:
                filters.append({"field": "revenue_growth_yoy", "op": ">", "value": 0})
            break
    
    # Parse EBITDA growth Y-o-Y
    ebitda_patterns = [
        (r'ebitda\s*(?:is\s+)?growing', '>', 0),
        (r'ebitda\s+growth\s*[>]\s*(\d+(?:\.\d+)?)', '>', None),
        (r'positive\s+ebitda\s+growth', '>', 0),
        (r'ebitda\s+(?:not\s+)?shrinking', '>', 0),
    ]
    
    for pattern, op, default in ebitda_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex and match.group(1) else default
                if value is None:
                    value = 0
                filters.append({"field": "ebitda_growth_yoy", "op": op, "value": value})
            except:
                filters.append({"field": "ebitda_growth_yoy", "op": ">", "value": 0})
            break
    
    # Check for combined "revenues and ebitda are growing"
    if re.search(r'revenues?\s+and\s+ebitda\s+(?:are\s+)?growing', query_lower):
        # Make sure both are added
        if not any(f["field"] == "revenue_growth_yoy" for f in filters):
            filters.append({"field": "revenue_growth_yoy", "op": ">", "value": 0})
        if not any(f["field"] == "ebitda_growth_yoy" for f in filters):
            filters.append({"field": "ebitda_growth_yoy", "op": ">", "value": 0})
    
    # Parse likely to beat earnings
    beat_patterns = [
        r'likely\s+(?:to\s+)?beat\s+(?:their\s+)?(?:next\s+)?earnings?\s*(?:estimates?)?',
        r'(?:will\s+)?(?:probably|likely)\s+beat\s+(?:earnings?|estimates?)',
        r'beat\s+(?:their\s+)?(?:next\s+)?earnings?\s+estimates?',
        r'expected\s+to\s+beat',
    ]
    
    for pattern in beat_patterns:
        if re.search(pattern, query_lower):
            filters.append({"field": "likely_to_beat", "op": "=", "value": True})
            break
    
    # Parse earnings within 30 days
    earnings_date_patterns = [
        r'(?:next\s+)?(?:quarterly\s+)?earnings?\s+(?:call\s+)?(?:is\s+)?(?:scheduled\s+)?within\s+(?:the\s+)?(?:next\s+)?30\s+days?',
        r'earnings?\s+(?:call\s+)?(?:in|within)\s+(?:the\s+)?(?:next\s+)?30\s+days?',
        r'upcoming\s+earnings?\s+(?:call|report)',
        r'earnings?\s+(?:report|call)\s+(?:coming\s+)?soon',
    ]
    
    for pattern in earnings_date_patterns:
        if re.search(pattern, query_lower):
            filters.append({"field": "earnings_within_30_days", "op": "=", "value": True})
            break
    
    # ========== EXISTING CRITERIA (Updated) ==========
    
    # Parse PE ratio conditions (comprehensive patterns)
    pe_patterns = [
        (r'pe\s*(?:ratio)?\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'pe\s*(?:ratio)?\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'pe\s*(?:ratio)?\s*<=\s*(\d+(?:\.\d+)?)', '<='),
        (r'pe\s*(?:ratio)?\s*>=\s*(\d+(?:\.\d+)?)', '>='),
        (r'pe\s*(?:ratio)?\s*(?:less\s+than|under|below)\s*(\d+(?:\.\d+)?)', '<'),
        (r'pe\s*(?:ratio)?\s*(?:greater\s+than|above|over)\s*(\d+(?:\.\d+)?)', '>'),
        (r'pe\s*(?:below|under|less\s+than)\s*(\d+(?:\.\d+)?)', '<'),
        (r'pe\s*(?:above|over|greater\s+than)\s*(\d+(?:\.\d+)?)', '>'),
        (r'low\s+pe', '<'),  # Will use default value
    ]
    
    for pattern, op in pe_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex else 20
                filters.append({"field": "pe_ratio", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse promoter holding conditions
    promoter_patterns = [
        (r'promoter\s*(?:holding)?\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'promoter\s*(?:holding)?\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'promoter\s*(?:holding)?\s*>=\s*(\d+(?:\.\d+)?)', '>='),
        (r'promoter\s*(?:holding)?\s*<=\s*(\d+(?:\.\d+)?)', '<='),
        (r'promoter\s*(?:holding)?\s*(?:greater\s+than|above|over)\s*(\d+(?:\.\d+)?)', '>'),
        (r'promoter\s*(?:holding)?\s*(?:less\s+than|under|below)\s*(\d+(?:\.\d+)?)', '<'),
        (r'high\s+promoter', '>'),  # Default to > 50
    ]
    
    for pattern, op in promoter_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex else 50
                filters.append({"field": "promoter_holding", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse positive earnings for last 4 quarters
    earnings_patterns = [
        r'positive\s+earnings?\s+(?:for\s+)?(?:the\s+)?(?:last\s+)?(?:4|four)\s+quarters?',
        r'(?:4|four)\s+quarters?\s+(?:of\s+)?positive\s+earnings?',
        r'consistent\s+(?:positive\s+)?earnings?',
        r'profitable\s+(?:for\s+)?(?:last\s+)?(?:4|four)\s+quarters?',
    ]
    
    for pattern in earnings_patterns:
        if re.search(pattern, query_lower):
            # All 4 quarters must be positive
            filters.append({"field": "q1_earnings", "op": ">", "value": 0})
            filters.append({"field": "q2_earnings", "op": ">", "value": 0})
            filters.append({"field": "q3_earnings", "op": ">", "value": 0})
            filters.append({"field": "q4_earnings", "op": ">", "value": 0})
            break
    
    # Parse EPS conditions
    eps_patterns = [
        (r'eps\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'eps\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'eps\s*(?:greater\s+than|above|over)\s*(\d+(?:\.\d+)?)', '>'),
        (r'eps\s*(?:less\s+than|under|below)\s*(\d+(?:\.\d+)?)', '<'),
        (r'positive\s+eps', '>'),
    ]
    
    for pattern, op in eps_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex else 0
                filters.append({"field": "eps", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse ROE (Return on Equity) conditions
    roe_patterns = [
        (r'roe\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'roe\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'roe\s*(?:greater\s+than|above|over)\s*(\d+(?:\.\d+)?)', '>'),
        (r'roe\s*(?:less\s+than|under|below)\s*(\d+(?:\.\d+)?)', '<'),
        (r'(?:return\s+on\s+equity)\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'high\s+roe', '>'),
    ]
    
    for pattern, op in roe_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex else 15
                filters.append({"field": "roe", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse dividend yield conditions
    dividend_patterns = [
        (r'dividend\s*(?:yield)?\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'dividend\s*(?:yield)?\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'dividend\s*(?:yield)?\s*(?:greater\s+than|above|over)\s*(\d+(?:\.\d+)?)', '>'),
        (r'high\s+dividend', '>'),
    ]
    
    for pattern, op in dividend_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex else 2
                filters.append({"field": "dividend_yield", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse debt to equity conditions
    debt_patterns = [
        (r'debt\s*(?:to\s*)?equity\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'debt\s*(?:to\s*)?equity\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'(?:low|minimal)\s+debt', '<'),
        (r'd/?e\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
    ]
    
    for pattern, op in debt_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex else 1.0
                filters.append({"field": "debt_to_equity", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse price conditions
    price_patterns = [
        (r'price\s*[<]\s*\$?₹?(\d+(?:\.\d+)?)', '<'),
        (r'price\s*[>]\s*\$?₹?(\d+(?:\.\d+)?)', '>'),
        (r'price\s*(?:less\s+than|under|below)\s*\$?₹?(\d+(?:\.\d+)?)', '<'),
        (r'price\s*(?:greater\s+than|above|over)\s*\$?₹?(\d+(?:\.\d+)?)', '>'),
    ]
    
    for pattern, op in price_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1))
                filters.append({"field": "price", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse market cap
    mcap_patterns = [
        (r'market\s*cap\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'market\s*cap\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'large\s*cap', '>'),
        (r'small\s*cap', '<'),
        (r'mid\s*cap', 'between'),
    ]
    
    for pattern, op in mcap_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                if op == 'between':
                    filters.append({"field": "market_cap", "op": ">", "value": 5000000})
                    filters.append({"field": "market_cap", "op": "<", "value": 20000000})
                else:
                    value = float(match.group(1)) if match.lastindex else (10000000 if op == '>' else 5000000)
                    filters.append({"field": "market_cap", "op": op, "value": value})
            except:
                pass
            break
    
    # Parse buyback
    if 'buyback' in query_lower:
        has_buyback = 'no buyback' not in query_lower and 'without buyback' not in query_lower
        filters.append({"field": "has_buyback", "op": "=", "value": has_buyback})
    
    # Parse revenue growth
    growth_patterns = [
        (r'(?:revenue\s*)?growth\s*[>]\s*(\d+(?:\.\d+)?)', '>'),
        (r'(?:revenue\s*)?growth\s*[<]\s*(\d+(?:\.\d+)?)', '<'),
        (r'high\s+growth', '>'),
    ]
    
    for pattern, op in growth_patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                value = float(match.group(1)) if match.lastindex else 20
                filters.append({"field": "revenue_growth", "op": op, "value": value})
            except:
                pass
            break
    
    return {"filters": filters}
