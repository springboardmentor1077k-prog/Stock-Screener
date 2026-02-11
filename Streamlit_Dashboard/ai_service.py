import re

class AIBackend:
    def __init__(self):
        self.invalid_keywords = [
            "predict", "forecast", "future", "future growth", "next quarter", "next year",
            "guarantee", "recommended", "recommendation",
            "should i buy", "strong buy", "good buy", "buy", "sell", "advice"
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
                print(f"COMPLIANCE REJECT: {keyword}")
                return {
                    "is_valid": False,
                    "errorCode": "unsupported_query"
                }

        # 2. SQL Generation Layer (Rule-based for Demo Stability)
        try:
            sql_query = self._generate_sql(user_query_lower)
            return {
                "is_valid": True,
                "generated_sql": sql_query,
                "explanation": self._generate_explanation(user_query)
            }
        except Exception as e:
            # Fallback for queries that don't match any known pattern but aren't explicitly invalid
            return {
                "is_valid": False,
                "errorCode": "unsupported_query"
            }

    def _generate_sql(self, query):
        """
        Generates SQL based on simple pattern matching.
        Defaults to SELECT * FROM stocks if no filters found, 
        but tries to apply WHERE clauses based on input.
        """
        base_sql = "SELECT * FROM stocks"
        conditions = []

        # Pattern: Sector filtering
        # e.g. "IT sector", "Finance sector"
        # Expanded sector list based on typical DB values
        sectors = ['it', 'finance', 'healthcare', 'energy', 'consumer discretionary', 'industrials', 'materials', 'utilities']
        for sector in sectors:
            if sector in query:
                # Capitalize correctly for DB match
                db_sector = sector.title()
                if sector == 'it': db_sector = 'IT' 
                if sector == 'consumer discretionary': db_sector = 'Consumer Discretionary'
                
                conditions.append(f"sector = '{db_sector}'")

        # Pattern: Numeric comparisons
        # Regex to find "metric condition value"
        # Metrics: pe ratio, market cap, price
        metrics = {
            "pe ratio": "pe_ratio",
            "market cap": "market_cap",
            "price": "price"
        }
        
        # Operators
        # greater than, above, >
        # less than, under, <
        
        for metric_phrase, col_name in metrics.items():
            if metric_phrase in query:
                # Check for "greater than" type
                if re.search(r'(greater than|above|more than|>)', query):
                    # Extract number
                    number = self._extract_number(query, metric_phrase)
                    if number is not None:
                        conditions.append(f"{col_name} > {number}")
                
                # Check for "less than" type
                elif re.search(r'(less than|below|under|<)', query):
                    number = self._extract_number(query, metric_phrase)
                    if number is not None:
                        conditions.append(f"{col_name} < {number}")
                        
                # Check for "equal" type (simplified)
                elif re.search(r'(equal to|=)', query):
                     number = self._extract_number(query, metric_phrase)
                     if number is not None:
                        conditions.append(f"{col_name} = {number}")

        # Construct final SQL
        if conditions:
            base_sql += " WHERE " + " AND ".join(conditions)
        
        # Add limit to prevent massive dumps in demo if not specific
        # base_sql += " LIMIT 50"
        
        return base_sql

    def _extract_number(self, query, context_phrase):
        """
        Attempts to find a number appearing after a context phrase.
        This is a heuristic.
        """
        try:
            # Find the part of string after the metric
            part_after = query.split(context_phrase)[1]
            # Find the first float/int number
            match = re.search(r'\d+(\.\d+)?', part_after)
            if match:
                return float(match.group())
        except:
            return None
        return None

    def _generate_explanation(self, query):
        return f"Translated natural language query '{query}' into SQL SELECT statement."
