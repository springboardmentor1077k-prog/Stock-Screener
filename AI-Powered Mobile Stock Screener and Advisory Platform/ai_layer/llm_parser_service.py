# AI/LLM Parser Service for Stock Screener
from typing import Dict, Any, List
import re
import sys
import os
from pathlib import Path

# Add backend to the Python path so we can import models
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.models.schemas import (
    ScreenerDSL,
    ScreenerRule,
    Condition,
    ConditionOperator,
    FinancialMetric,
    Exchange,
)
import logging

logger = logging.getLogger(__name__)

class LLMParserService:
    def __init__(self):
        # Define mappings for financial metrics
        self.metric_mappings = {
            'pe': 'pe_ratio',
            'pe ratio': 'pe_ratio',
            'price to earnings': 'pe_ratio',
            'peg': 'peg_ratio',
            'peg ratio': 'peg_ratio',
            'pe growth': 'peg_ratio',
            'ebitda': 'ebitda',
            'earnings before interest taxes depreciation amortization': 'ebitda',
            'free cash flow': 'free_cash_flow',
            'free cash': 'free_cash_flow',
            'cash flow': 'free_cash_flow',
            'debt to free cash flow': 'debt_to_free_cash_flow',
            'debt to cash': 'debt_to_free_cash_flow',
            'promoter holding': 'promoter_holding',
            'promoter': 'promoter_holding',
            'revenue growth': 'revenue_growth_yoy',
            'revenue growth yoy': 'revenue_growth_yoy',
            'ebitda growth': 'ebitda_growth_yoy',
            'ebitda growth yoy': 'ebitda_growth_yoy',
            'earnings growth': 'earnings_growth_yoy',
            'earnings growth yoy': 'earnings_growth_yoy',
            'current price': 'current_price',
            'price': 'current_price',
            'market cap': 'market_cap',
            'eps': 'eps',
            'earnings per share': 'eps',
            'book value': 'book_value',
            'roe': 'roe',
            'roa': 'roa',
            'return on equity': 'roe',
            'return on assets': 'roa',
            'dividend yield': 'dividend_yield'
        }
        
        # Define operator mappings
        self.operator_mappings = {
            'greater than': 'GREATER_THAN',
            'gt': 'GREATER_THAN',
            'above': 'GREATER_THAN',
            'over': 'GREATER_THAN',
            'higher than': 'GREATER_THAN',
            'less than': 'LESS_THAN',
            'lt': 'LESS_THAN',
            'below': 'LESS_THAN',
            'under': 'LESS_THAN',
            'lower than': 'LESS_THAN',
            'equals': 'EQUALS',
            'equal': 'EQUALS',
            'is': 'EQUALS',
            'equals to': 'EQUALS',
            'equal to': 'EQUALS',
            'greater than or equal': 'GREATER_THAN_OR_EQUAL',
            'gte': 'GREATER_THAN_OR_EQUAL',
            'at least': 'GREATER_THAN_OR_EQUAL',
            'less than or equal': 'LESS_THAN_OR_EQUAL',
            'lte': 'LESS_THAN_OR_EQUAL',
            'at most': 'LESS_THAN_OR_EQUAL',
            'not equals': 'NOT_EQUALS',
            'not equal': 'NOT_EQUALS',
            'different from': 'NOT_EQUALS'
        }
        
        # Define exchange mappings
        self.exchange_mappings = {
            'nse': 'NSE',
            'bse': 'BSE',
            'nyse': 'NYSE',
            'nasdaq': 'NASDAQ'
        }
        
        # Define sector mappings - use word boundaries to avoid partial matches
        self.sector_mappings = {
            'information technology': 'Information Technology',
            'it': 'Information Technology',
            'banking': 'Banking',
            'finance': 'Finance',
            'automobile': 'Automobile',
            'auto': 'Automobile',
            'pharma': 'Pharmaceuticals',
            'pharmaceuticals': 'Pharmaceuticals',
            'healthcare': 'Healthcare',
            'energy': 'Energy',
            'oil': 'Energy',
            'gas': 'Energy',
            'telecom': 'Telecommunications',
            'telecommunications': 'Telecommunications',
            'retail': 'Retail',
            'consumer goods': 'Consumer Goods',
            'fmcg': 'Consumer Goods'
        }

    def parse_query(self, query: str) -> ScreenerDSL:
        """
        Parse a natural language query and convert it to structured DSL.
        """
        logger.info(f"Parsing query: {query}")
        
        # Convert to lowercase for easier processing
        query_lower = query.lower().strip()
        
        # Initialize DSL components
        name = "Generated Query"
        description = query
        rules = []
        exchanges = []
        sectors = []
        industries = []
        
        # Extract exchanges from query using word boundaries
        for exchange_key, exchange_value in self.exchange_mappings.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(exchange_key) + r'\b'
            if re.search(pattern, query_lower):
                exchanges.append(Exchange[exchange_value])
        
        # Extract sectors from query using word boundaries
        for sector_key, sector_value in self.sector_mappings.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(sector_key) + r'\b'
            if re.search(pattern, query_lower):
                sectors.append(sector_value)
        
        # Parse conditions from the query
        conditions = self._extract_conditions(query_lower)
        
        if conditions:
            # Create a rule with the extracted conditions
            rule = ScreenerRule(
                conditions=conditions,
                logical_operator="AND"
            )
            rules.append(rule)
        
        # Create and return the DSL object
        dsl = ScreenerDSL(
            name=name,
            description=description,
            rules=rules,
            exchanges=exchanges if exchanges else None,
            sectors=sectors if sectors else None,
            industries=industries if industries else None
        )
        
        logger.info(f"Generated DSL: {dsl}")
        return dsl

    def _extract_conditions(self, query: str) -> List[Condition]:
        """
        Extract conditions from the natural language query.
        """
        conditions = []
        
        # Sort metrics by length in descending order to match longer phrases first
        sorted_metrics = sorted(self.metric_mappings.items(), key=lambda x: len(x[0]), reverse=True)
        
        for metric_key, metric_value in sorted_metrics:
            # Find all instances of the metric in the query
            escaped_metric = re.escape(metric_key)
            metric_positions = [(m.start(), m.end()) for m in re.finditer(r'\b' + escaped_metric + r'\b', query, re.IGNORECASE)]
            
            for start_pos, end_pos in metric_positions:
                # Get the substring after the metric
                after_metric = query[end_pos:].strip()
                
                # Look for operator-value pattern in the remaining text
                # Try to match various operator formats
                matched = False
                for op_key, op_value in self.operator_mappings.items():
                    escaped_op = re.escape(op_key)
                    # Look for the operator followed by a space and then the value
                    op_pattern = r'^\b' + escaped_op + r'\b\s*(\d+\.?\d*)'
                    op_match = re.match(op_pattern, after_metric, re.IGNORECASE)
                    
                    if op_match and op_match.group(1).strip():  # Make sure we captured a value
                        value_text = op_match.group(1)
                        try:
                            value = float(value_text)
                            
                            # Validate metric is in FinancialMetric enum
                            try:
                                # Convert to uppercase and underscore format to match enum
                                financial_metric = FinancialMetric[metric_value.upper()]
                                condition_operator = ConditionOperator[op_value]
                                
                                condition = Condition(
                                    field=financial_metric,
                                    operator=condition_operator,
                                    value=value
                                )
                                conditions.append(condition)
                                matched = True
                                break  # Move to the next metric occurrence after finding a match
                            except KeyError:
                                logger.warning(f"Invalid metric or operator: {metric_value}, {op_value}")
                                continue
                        except ValueError:
                            logger.warning(f"Could not convert value to float: {value_text}")
                            continue
                
                # If no operator was matched, try other patterns
                if not matched:
                    # Try to match a simple numeric value after the metric
                    # This pattern looks for a number after the operator
                    simple_pattern = r'(\d+\.?\d*)'
                    simple_match = re.match(simple_pattern, after_metric.strip(), re.IGNORECASE)
                    
                    if simple_match:
                        # We need to determine the operator from the context
                        # Look for the best operator match in the text between the metric and the number
                        text_between = query[start_pos:end_pos+len(after_metric)].lower()
                        
                        # Find the operator that appears in the text between metric and value
                        best_op_key = None
                        best_op_value = None
                        best_pos = -1
                        
                        for op_key, op_value in self.operator_mappings.items():
                            pos = text_between.find(op_key.lower())
                            if pos != -1 and (best_pos == -1 or pos < best_pos):
                                best_pos = pos
                                best_op_key = op_key
                                best_op_value = op_value
                        
                        if best_op_key and best_op_value:
                            value_text = simple_match.group(1)
                            try:
                                value = float(value_text)
                                
                                # Validate metric is in FinancialMetric enum
                                try:
                                    # Convert to uppercase and underscore format to match enum
                                    financial_metric = FinancialMetric[metric_value.upper()]
                                    condition_operator = ConditionOperator[best_op_value]
                                    
                                    condition = Condition(
                                        field=financial_metric,
                                        operator=condition_operator,
                                        value=value
                                    )
                                    conditions.append(condition)
                                    matched = True
                                except KeyError:
                                    logger.warning(f"Invalid metric or operator: {metric_value}, {best_op_value}")
                                    continue
                            except ValueError:
                                logger.warning(f"Could not convert value to float: {value_text}")

        # Handle some common specific patterns that might not match the general regex
        conditions.extend(self._handle_specific_patterns(query))
        
        return conditions

    def _handle_specific_patterns(self, query: str) -> List[Condition]:
        """
        Handle specific query patterns that don't match the general regex.
        """
        conditions = []
        
        # Handle "between" patterns like "PE between 10 and 20"
        for metric_key, metric_value in sorted(self.metric_mappings.items(), key=lambda x: len(x[0]), reverse=True):
            # Use word boundaries for the metric to avoid partial matches
            escaped_metric = re.escape(metric_key)
            between_pattern = r'\b' + escaped_metric + r'\b\s+between\s+(\d+\.?\d*)\s+and\s+(\d+\.?\d*)'
            between_matches = re.findall(between_pattern, query, re.IGNORECASE)
            
            for match in between_matches:
                lower_value = float(match[0])
                upper_value = float(match[1])
                
                try:
                    financial_metric = FinancialMetric[metric_value.upper()]
                    
                    # For between, we'll create two conditions (greater than or equal to lower and less than or equal to upper)
                    condition1 = Condition(
                        field=financial_metric,
                        operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                        value=lower_value
                    )
                    condition2 = Condition(
                        field=financial_metric,
                        operator=ConditionOperator.LESS_THAN_OR_EQUAL,
                        value=upper_value
                    )
                    
                    conditions.extend([condition1, condition2])
                except KeyError:
                    logger.warning(f"Invalid metric for between pattern: {metric_value}")
        
        # Handle "positive" patterns like "positive free cash flow"
        for metric_key, metric_value in self.metric_mappings.items():
            escaped_metric = re.escape(metric_key)
            positive_pattern = r'positive\s+\b' + escaped_metric + r'\b'
            if re.search(positive_pattern, query, re.IGNORECASE):
                try:
                    financial_metric = FinancialMetric[metric_value.upper()]
                    condition = Condition(
                        field=financial_metric,
                        operator=ConditionOperator.GREATER_THAN,
                        value=0.0
                    )
                    conditions.append(condition)
                except KeyError:
                    logger.warning(f"Invalid metric for positive pattern: {metric_value}")
        
        # Handle "negative" patterns
        for metric_key, metric_value in self.metric_mappings.items():
            escaped_metric = re.escape(metric_key)
            negative_pattern = r'negative\s+\b' + escaped_metric + r'\b'
            if re.search(negative_pattern, query, re.IGNORECASE):
                try:
                    financial_metric = FinancialMetric[metric_value.upper()]
                    condition = Condition(
                        field=financial_metric,
                        operator=ConditionOperator.LESS_THAN,
                        value=0.0
                    )
                    conditions.append(condition)
                except KeyError:
                    logger.warning(f"Invalid metric for negative pattern: {metric_value}")
        
        return conditions

# Global instance of the parser service
llm_parser_service = LLMParserService()

def parse_natural_language_query(query: str) -> ScreenerDSL:
    """
    Public function to parse a natural language query to structured DSL.
    """
    return llm_parser_service.parse_query(query)

if __name__ == "__main__":
    # Test the parser with some example queries
    test_queries = [
        "Show me all NSE stocks with PE below 15 and promoter holding above 50",
        "Find stocks with PEG ratio less than 1 and positive free cash flow",
        "Show me IT companies with revenue growth above 15% YoY",
        "Give me stocks with PE ratio between 10 and 20",
        "Show stocks with debt to free cash flow below 3"
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        try:
            dsl = parse_natural_language_query(query)
            print(f"DSL: {dsl}")
            print("---")
        except Exception as e:
            print(f"Error parsing query: {e}")
            print("---")