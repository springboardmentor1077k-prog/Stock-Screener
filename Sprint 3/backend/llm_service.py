import re
import json
import logging
from typing import Dict, Any

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def nl_to_dsl(nl_query: str, mode: str = "query") -> Dict[str, Any]:
    """
    Translates Natural Language to Nested DSL using Regex (Offline Mode).
    Updated to support 'BETWEEN', 'PEG', and smarter parsing.
    """
    q = nl_query.lower()
    logger.info(f"Processing query (Offline Mode): {nl_query}")

    # --- 1. HANDLE "EXPLAIN" MODE ---
    if mode == "explain":
        return "This is a generated summary of your stock screening results. (Offline Mode)"

    # --- 2. HANDLE "OR" LOGIC (NESTED) ---
    if " or " in q:
        parts = q.split(" or ")
        filters = []
        for part in parts:
            filters.append({
                "logic": "AND",
                "filters": _parse_simple_conditions(part)
            })
        return {"logic": "OR", "filters": filters}

    # --- 3. HANDLE "AND" LOGIC (SIMPLE) ---
    return {
        "logic": "AND",
        "filters": _parse_simple_conditions(q)
    }

def _parse_simple_conditions(text: str):
    """Helper to extract field/operator/value from a string segment."""
    conditions = []
    text = text.lower()

    # --- 1. SECTOR DETECTION ---
    if "tech" in text:
        conditions.append({"field": "sector", "operator": "=", "value": "Technology"})
    elif "energy" in text:
        conditions.append({"field": "sector", "operator": "=", "value": "Energy"})
    elif "finance" in text:
        conditions.append({"field": "sector", "operator": "=", "value": "Finance"})
    elif "health" in text:
        conditions.append({"field": "sector", "operator": "=", "value": "Healthcare"})
    elif "consumer" in text:
         conditions.append({"field": "sector", "operator": "=", "value": "Consumer Defensive"})

    # --- 2. PE RATIO (With BETWEEN support) ---
    # Pattern: "PE between 15 and 30"
    pe_between = re.search(r'pe\s*.*\s*between\s*(\d+)\s*and\s*(\d+)', text)
    if pe_between:
        low = float(pe_between.group(1))
        high = float(pe_between.group(2))
        conditions.append({"field": "pe_ratio", "operator": "between", "value": [low, high]})
    else:
        # Pattern: "PE < 30"
        pe_match = re.search(r'pe\s*([<>])\s*(\d+)', text)
        if pe_match:
            op = pe_match.group(1)
            val = float(pe_match.group(2))
            conditions.append({"field": "pe_ratio", "operator": op, "value": val})

    # --- 3. PEG RATIO (New!) ---
    # Pattern: "PEG < 2"
    peg_match = re.search(r'peg\s*.*\s*([<>])\s*(\d+(\.\d+)?)', text)
    if peg_match:
        op = peg_match.group(1)
        val = float(peg_match.group(2))
        conditions.append({"field": "peg_ratio", "operator": op, "value": val})

    # --- 4. DIVIDEND ---
    div_match = re.search(r'dividend\s*([<>])\s*(\d+)', text)
    if div_match:
        op = div_match.group(1)
        val = float(div_match.group(2))
        conditions.append({"field": "dividend_yield", "operator": op, "value": val})

    # --- 5. PROFIT ---
    profit_match = re.search(r'profit\s*([<>])\s*(\d+)', text)
    if profit_match:
        op = profit_match.group(1)
        val = float(profit_match.group(2))
        conditions.append({"field": "net_profit", "operator": op, "value": val, "quarters": 1})

    # DEFAULT FALLBACK (If nothing found, assume Tech to avoid empty query)
    if not conditions:
        conditions.append({"field": "sector", "operator": "=", "value": "Technology"})

    return conditions