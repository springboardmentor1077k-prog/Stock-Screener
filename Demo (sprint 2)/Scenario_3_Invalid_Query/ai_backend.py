import re

class AIBackend:
    def __init__(self):
        self.invalid_keywords = [
            "predict", "forecast", "future", "next quarter", "next year",
            "boom", "will grow", "should i buy", "advice", "recommend"
        ]

    def process_query(self, user_query):
        """
        Main entry point for the AI backend.
        Input: Natural language query string.
        Output: JSON-like dictionary with status, SQL (if valid), or error (if invalid).
        """
        user_query_lower = user_query.lower()

        # 1. Validation Layer
        for keyword in self.invalid_keywords:
            if keyword in user_query_lower:
                return {
                    "is_valid": False,
                    "error_message": "Invalid or unsupported query",
                    "reason": f"Queries related to '{keyword}' are not supported. This system supports only descriptive data queries."
                }

        # 2. SQL Generation Layer (Rule-based for Demo Stability)
        try:
            sql_query = self._generate_sql(user_query)
            return {
                "is_valid": True,
                "generated_sql": sql_query,
                "explanation": self._generate_explanation(user_query)
            }
        except Exception as e:
            # Fallback for queries that don't match any known pattern but aren't explicitly invalid
            return {
                "is_valid": False,
                "error_message": "Could not understand query structure",
                "reason": f"The query structure is too complex or ambiguous for this demo. Error: {str(e)}"
            }

    def _generate_sql(self, query):
        """
        Generates SQL based on improved pattern matching.
        """
        base_sql = "SELECT * FROM stocks"
        conditions = []
        query_lower = query.lower()

        # --- 1. Sector Logic ---
        sectors = {
            'it': 'IT', 'tech': 'IT', 'technology': 'IT',
            'finance': 'Finance', 'financial': 'Finance', 'banking': 'Finance', 'banks': 'Finance',
            'healthcare': 'Healthcare', 'health': 'Healthcare', 'medical': 'Healthcare',
            'energy': 'Energy', 'oil': 'Energy', 'gas': 'Energy',
            'consumer': 'Consumer Discretionary', 'retail': 'Consumer Discretionary'
        }
        
        found_sectors = set()
        for key, val in sectors.items():
            # Check for whole word match to avoid partials like 'health' in 'healthy'
            if re.search(fr'\b{key}\b', query_lower):
                found_sectors.add(val)
        
        if found_sectors:
            sector_conditions = [f"sector = '{s}'" for s in found_sectors]
            if len(sector_conditions) > 1:
                 conditions.append(f"({' OR '.join(sector_conditions)})")
            else:
                 conditions.append(sector_conditions[0])

        # --- 2. Numeric Logic (Price, PE, Market Cap) ---
        metric_map = {
            'pe ratio': 'pe_ratio', 'p/e': 'pe_ratio', 'pe': 'pe_ratio',
            'market cap': 'market_cap', 'cap': 'market_cap',
            'price': 'price', 'cost': 'price', 'value': 'price'
        }
        
        # Sort keys by length descending to match longer phrases first (e.g. "pe ratio" before "pe")
        sorted_metrics = sorted(metric_map.keys(), key=len, reverse=True)
        
        # Track which columns we already have a condition for to avoid duplicates
        # e.g. "pe ratio" matches "pe" and "pe ratio", we only want one condition for pe_ratio
        processed_columns = set()

        # Let's rewrite the numeric logic block to consume the string
        temp_query = query_lower
        
        for metric_term in sorted_metrics:
            if re.search(fr'\b{re.escape(metric_term)}\b', temp_query):
                col = metric_map[metric_term]
                
                # Check for "between" logic first
                between_match = re.search(fr'\b{re.escape(metric_term)}\b.*?between\s*(\d+(\.\d+)?)\s*and\s*(\d+(\.\d+)?)', temp_query)
                if between_match:
                    val1 = float(between_match.group(1))
                    val3 = float(between_match.group(3))
                    conditions.append(f"{col} BETWEEN {val1} AND {val3}")
                    # Remove the processed part to avoid re-matching
                    temp_query = temp_query.replace(between_match.group(0), " ")
                    continue

                # Find number after the metric
                # Look for > < = logic
                # We need to extract the number associated with THIS metric term instance
                
                # Simplification: Just look ahead from the metric term
                # Regex that matches: metric_term + optional words + operator + number
                # Or metric_term + optional words + number (implicit equality)
                
                # Operators
                op_regex = r'(>|above|greater|more|over|<|below|less|under|=|is|equal|at)?'
                # Number
                num_regex = r'\s*(\d+(\.\d+)?)'
                
                # Combined regex to find the pattern
                # We use specific regex for this metric term
                pattern = re.compile(fr'\b{re.escape(metric_term)}\b\s*(?:is|are|was|were)?\s*(?P<op>>|above|greater|more|over|<|below|less|under|=|is|equal|at)?\s*(?:than|to)?\s*(?P<num>\d+(\.\d+)?)')
                
                match = pattern.search(temp_query)
                if match:
                    num = float(match.group('num'))
                    op_str = match.group('op')
                    
                    if op_str in ['>', 'above', 'greater', 'more', 'over']:
                        conditions.append(f"{col} > {num}")
                    elif op_str in ['<', 'below', 'less', 'under']:
                        conditions.append(f"{col} < {num}")
                    else:
                        # implicit or explicit equal
                        conditions.append(f"{col} = {num}")
                    
                    # Remove the matched part
                    temp_query = temp_query.replace(match.group(0), " ")



        # --- 3. Company/Symbol Logic ---
        # Known entities map for the demo
        known_companies = {
            'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'alphabet': 'GOOGL', 
            'nvidia': 'NVDA', 'tesla': 'TSLA', 'amazon': 'AMZN', 'visa': 'V',
            'jpmorgan': 'JPM', 'chase': 'JPM', 'bank of america': 'BAC', 'bac': 'BAC',
            'pfizer': 'PFE', 'johnson': 'JNJ', 'exxon': 'XOM', 'chevron': 'CVX',
            'oracle': 'ORCL', 'cisco': 'CSCO', 'adobe': 'ADBE', 'salesforce': 'CRM',
            'intel': 'INTC', 'amd': 'AMD', 'wells fargo': 'WFC', 'citi': 'C', 'citigroup': 'C',
            'goldman': 'GS', 'morgan stanley': 'MS', 'amex': 'AXP', 'american express': 'AXP',
            'unitedhealth': 'UNH', 'lilly': 'LLY', 'eli lilly': 'LLY', 'abbvie': 'ABBV',
            'merck': 'MRK', 'thermo': 'TMO', 'shell': 'SHEL', 'total': 'TTE',
            'conoco': 'COP', 'schlumberger': 'SLB', 'eog': 'EOG', 'home depot': 'HD',
            'mcdonalds': 'MCD', 'nike': 'NKE', 'starbucks': 'SBUX'
        }

        for name, symbol in known_companies.items():
            if re.search(fr'\b{name}\b', query_lower):
                conditions.append(f"(symbol = '{symbol}' OR company_name LIKE '%{name}%')")

        # Construct final SQL
        if conditions:
            base_sql += " WHERE " + " AND ".join(conditions)
        
        # Add limit to prevent massive dumps
        base_sql += " LIMIT 50"
        
        return base_sql

    def _extract_number(self, query, context_phrase):
        """
        Attempts to find a number appearing after a context phrase.
        """
        try:
            # Find the part of string after the metric
            parts = query.split(context_phrase, 1)
            if len(parts) > 1:
                part_after = parts[1]
                # Find the first float/int number
                match = re.search(r'(\d+(\.\d+)?)', part_after)
                if match:
                    return float(match.group(1))
        except:
            return None
        return None

    def _generate_explanation(self, query):
        return f"Translated natural language query '{query}' into SQL SELECT statement."
