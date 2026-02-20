import re
import json
import logging
import random
from typing import Dict, Any, List

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def nl_to_dsl(nl_query: str, mode: str = "query") -> Dict[str, Any]:
    """
    Translates Natural Language to Nested DSL using Regex.
    Context-Aware: Applies the main sector to all parts of an 'OR' query.
    """
    q = nl_query.lower()
    logger.info(f"Processing query (Offline Mode): {nl_query}")

    # --- 1. HANDLE "EXPLAIN" MODE ---
    if mode == "explain":
        return "This is a generated summary of your stock screening results. (Offline Mode)"

    # --- 2. DETECT GLOBAL CONTEXT (SECTOR) ---
    # We look for the sector at the very start to apply it globally
    global_sector = None
    if "tech" in q: global_sector = "Technology"
    elif "energy" in q: global_sector = "Energy"
    elif "finance" in q: global_sector = "Finance"
    elif "health" in q: global_sector = "Healthcare"
    elif "consumer" in q: global_sector = "Consumer Defensive"

    # --- 3. HANDLE "OR" LOGIC (NESTED) ---
    if " or " in q:
        parts = q.split(" or ")
        filters = []
        for part in parts:
            # Parse the specific conditions in this part
            part_filters = _parse_simple_conditions(part)
            
            # CRITICAL FIX: If we found a global sector, force it into EVERY part
            # unless that part already specified a different sector.
            has_sector = any(f['field'] == 'sector' for f in part_filters)
            if global_sector and not has_sector:
                part_filters.insert(0, {"field": "sector", "operator": "=", "value": global_sector})
            
            filters.append({
                "logic": "AND",
                "filters": part_filters
            })
        return {"logic": "OR", "filters": filters}

    # --- 4. HANDLE "AND" LOGIC (SIMPLE) ---
    return {
        "logic": "AND",
        "filters": _parse_simple_conditions(q)
    }

def _parse_simple_conditions(text: str) -> List[Dict[str, Any]]:
    """Helper to extract field/operator/value from a string segment."""
    conditions = []
    text = text.lower()

    # --- 1. SECTOR DETECTION (Local) ---
    if "tech" in text: conditions.append({"field": "sector", "operator": "=", "value": "Technology"})
    elif "energy" in text: conditions.append({"field": "sector", "operator": "=", "value": "Energy"})
    elif "finance" in text: conditions.append({"field": "sector", "operator": "=", "value": "Finance"})
    elif "health" in text: conditions.append({"field": "sector", "operator": "=", "value": "Healthcare"})
    elif "consumer" in text: conditions.append({"field": "sector", "operator": "=", "value": "Consumer Defensive"})

    # --- HELPER: NORMALIZE OPERATORS ---
    # Less Than variants
    text = text.replace("less than", "<").replace("lower than", "<").replace("under", "<").replace("below", "<")
    # Greater Than variants
    text = text.replace("greater than", ">").replace("higher than", ">").replace("more than", ">").replace("over", ">").replace("above", ">")
    # Equal variants
    text = text.replace("equals", "=").replace("equal to", "=").replace(" is ", " = ") 

    # --- 2. PE RATIO ---
    pe_between = re.search(r'pe\s*.*\s*between\s*(\d+)\s*and\s*(\d+)', text)
    if pe_between:
        conditions.append({"field": "pe_ratio", "operator": "between", "value": [float(pe_between.group(1)), float(pe_between.group(2))]})
    else:
        pe_match = re.search(r'pe\s*.*([<>=])\s*(\d+(\.\d+)?)', text)
        if pe_match:
            conditions.append({"field": "pe_ratio", "operator": pe_match.group(1), "value": float(pe_match.group(2))})

    # --- 3. PEG RATIO ---
    peg_match = re.search(r'peg\s*.*([<>=])\s*(\d+(\.\d+)?)', text)
    if peg_match:
        conditions.append({"field": "peg_ratio", "operator": peg_match.group(1), "value": float(peg_match.group(2))})

    # --- 4. DIVIDEND ---
    div_match = re.search(r'dividend\s*.*([<>=])\s*(\d+(\.\d+)?)', text)
    if div_match:
        conditions.append({"field": "dividend_yield", "operator": div_match.group(1), "value": float(div_match.group(2))})

    # --- 5. PROFIT ---
    profit_match = re.search(r'profit\s*.*([<>=])\s*(\d+(\.\d+)?)', text)
    if profit_match:
        conditions.append({"field": "net_profit", "operator": profit_match.group(1), "value": float(profit_match.group(2)), "quarters": 1})

    # Default fallback handled by global context in main function now

    return conditions

def generate_market_insight(stocks: list) -> str:
    """
    Generates a dynamic 'AI' market analysis based on the specific list of stocks found.
    """
    if not stocks:
        return "⚠️ **Analysis Unavailable:** No data provided to analyze."

    # 1. ANALYZE DATA
    sectors = {}
    total_pe = 0
    valid_pe_count = 0
    highest_pe_stock = ("None", 0)
    lowest_pe_stock = ("None", 9999)
    
    for s in stocks:
        sec = s.get('sector', 'Unknown')
        sectors[sec] = sectors.get(sec, 0) + 1
        
        pe = s.get('pe_ratio')
        if pe:
            try:
                pe = float(pe)
                if pe > 0:
                    total_pe += pe
                    valid_pe_count += 1
                    if pe > highest_pe_stock[1]: highest_pe_stock = (s['ticker'], pe)
                    if pe < lowest_pe_stock[1]: lowest_pe_stock = (s['ticker'], pe)
            except: pass

    # 2. DERIVE INSIGHTS
    dominant_sector = max(sectors, key=sectors.get) if sectors else "Mixed"
    avg_pe = total_pe / valid_pe_count if valid_pe_count > 0 else 0
    
    # 3. CONSTRUCT NARRATIVE
    intros = [
        f"🔍 **Market Scan Report:** This screen is heavily weighted towards the **{dominant_sector}** sector.",
        f"📊 **Sector Analysis:** We are seeing strong consolidation in **{dominant_sector}**, which makes up the majority of these results.",
        f"⚡ **Trend Alert:** The AI has identified a cluster of opportunities primarily within **{dominant_sector}**."
    ]
    intro_text = random.choice(intros)

    if avg_pe < 15:
        val_text = f"📉 **Undervalued:** The average PE of **{avg_pe:.1f}** suggests these stocks are trading at a discount."
    elif avg_pe > 30:
        val_text = f"🚀 **High Growth Premium:** The group trades at a high average PE of **{avg_pe:.1f}**, indicating growth expectations."
    else:
        val_text = f"⚖️ **Fair Valuation:** With an average PE of **{avg_pe:.1f}**, this group is trading in line with historical averages."

    callout_text = ""
    if highest_pe_stock[0] != "None":
        callout_text = f"💎 **Outlier:** **{highest_pe_stock[0]}** commands the highest premium (PE {highest_pe_stock[1]:.1f}), while **{lowest_pe_stock[0]}** offers the deep value play (PE {lowest_pe_stock[1]:.1f})."

    conclusions = [
        "**Strategy:** Consider these for a diversified watch list.",
        "**Action:** Review individual balance sheets before entry.",
        "**Summary:** A solid mix of potential targets for this strategy."
    ]
    conclusion_text = random.choice(conclusions)

    return f"""
    ### 🧠 ProTrade AI Analysis
    
    {intro_text}
    
    {val_text}
    
    {callout_text}
    
    _{conclusion_text}_
    """