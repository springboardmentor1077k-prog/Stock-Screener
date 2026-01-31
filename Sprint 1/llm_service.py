from openai import OpenAI
import json
from typing import Dict, Any
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI()  # reads OPENAI_API_KEY automatically

def _mock_nl_to_dsl(user_query: str) -> Dict[str, Any]:
    """
    Mock LLM that extracts numeric values.
    Updated for DB Columns: revenue, net_profit, ebitda
    """
    query_lower = user_query.lower()
    conditions = []
    
    # ==========================================
    # 1. QUARTERLY LOGIC
    # ==========================================
    
    # A. Detect "Last N Quarters" (Default to 1)
    quarters = 1
    q_match = re.search(r'last\s*(\d+)\s*quarter', query_lower)
    if q_match:
        quarters = int(q_match.group(1))

    # B. Revenue Extraction
    rev_patterns = [
        (r'revenue\s*>\s*([\d.]+)', '>'),
        (r'revenue\s*<\s*([\d.]+)', '<'),
        (r'revenue\s*above\s*([\d.]+)', '>'),
        (r'revenue\s*below\s*([\d.]+)', '<'),
    ]
    for pattern, operator in rev_patterns:
        match = re.search(pattern, query_lower)
        if match:
            val = float(match.group(1))
            conditions.append({
                "field": "revenue", 
                "operator": operator, 
                "value": val, 
                "quarters": quarters
            })
            break

    # C. Net Profit Extraction (Matches "net profit" or "profit")
    np_patterns = [
        (r'(?:net\s*)?profit\s*>\s*([\d.]+)', '>'),
        (r'(?:net\s*)?profit\s*<\s*([\d.]+)', '<'),
        (r'(?:net\s*)?profit\s*above\s*([\d.]+)', '>'),
        (r'(?:net\s*)?profit\s*below\s*([\d.]+)', '<'),
    ]
    for pattern, operator in np_patterns:
        match = re.search(pattern, query_lower)
        if match:
            val = float(match.group(1))
            conditions.append({
                "field": "net_profit",  # Matches your DB column
                "operator": operator, 
                "value": val, 
                "quarters": quarters
            })
            break

    # D. EBITDA Extraction
    ebitda_patterns = [
        (r'ebitda\s*>\s*([\d.]+)', '>'),
        (r'ebitda\s*<\s*([\d.]+)', '<'),
    ]
    for pattern, operator in ebitda_patterns:
        match = re.search(pattern, query_lower)
        if match:
            val = float(match.group(1))
            conditions.append({
                "field": "ebitda",   # Matches your DB column
                "operator": operator, 
                "value": val, 
                "quarters": quarters
            })
            break

    # ==========================================
    # 2. STANDARD SECTOR & FUNDAMENTALS
    # ==========================================
    sector_map = {
        'technology': 'Technology', 'tech': 'Technology',
        'finance': 'Finance', 'healthcare': 'Healthcare', 'energy': 'Energy'
    }
    for keyword, sector in sector_map.items():
        if keyword in query_lower:
            conditions.append({"field": "sector", "operator": "=", "value": sector})
            break
    
    # PE Ratio
    pe_patterns = [(r'pe\s*<\s*([\d.]+)', '<'), (r'pe\s*>\s*([\d.]+)', '>')]
    for pattern, operator in pe_patterns:
        match = re.search(pattern, query_lower)
        if match:
            conditions.append({"field": "pe_ratio", "operator": operator, "value": float(match.group(1))})
            break

    # ==========================================
    # RETURN LOGIC
    # ==========================================
    if len(conditions) > 1:
        return {"and": conditions}
    elif len(conditions) == 1:
        return conditions[0]
    else:
        # Fallback default
        return {"field": "sector", "operator": "=", "value": "Technology"}

def nl_to_dsl(user_query: str) -> Dict[str, Any]:
    try:
        logger.info(f"Processing query: {user_query}")
        return _mock_nl_to_dsl(user_query)
    except Exception as e:
        logger.error(f"Error in nl_to_dsl: {str(e)}")
        return {"field": "sector", "operator": "=", "value": "Technology"}