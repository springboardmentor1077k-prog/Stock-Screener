import re

# =========================================================
# OPERATOR MAP
# =========================================================
OPERATOR_MAP = {
    "crosses above": "CROSS_ABOVE",
    "crosses below": "CROSS_BELOW",
    "greater than": ">",
    "less than": "<",
    "above": ">",
    "below": "<",
    "equal to": "==",
    "not equal to": "!="
}

# =========================================================
# INDICATOR ALIASES (small case + full form support)
# =========================================================
ALIASES = {

    # -------- VALUATION --------
    "PE": [
        "pe", "p e", "price to earnings", "price to earnings ratio",
        "price earnings", "price earnings ratio"
    ],
    "PB": ["pb", "price to book", "price to book ratio"],
    "PS": ["ps", "price to sales", "price to sales ratio"],
    "PEG": ["peg", "price earnings growth"],
    "MARKET_CAP": ["market cap", "market capitalization"],

    # -------- PROFITABILITY --------
    "ROE": ["roe", "return on equity"],
    "ROA": ["roa", "return on assets"],
    "ROCE": ["roce", "return on capital employed"],

    # -------- FINANCIAL HEALTH --------
    "DEBT_EQUITY": [
        "debt equity", "debt to equity", "debt to equity ratio"
    ],
    "CURRENT_RATIO": ["current ratio"],
    "QUICK_RATIO": ["quick ratio", "acid test ratio"],

    # -------- DIVIDEND --------
    "DIVIDEND_YIELD": ["dividend yield", "yield"],

    # -------- TECHNICAL --------
    "RSI": ["rsi", "relative strength index"],
    "MACD": ["macd", "moving average convergence divergence"],
    "ADX": ["adx", "average directional index"],

    # -------- MOVING AVERAGES --------
    "SMA": ["sma", "simple moving average"],
    "EMA": ["ema", "exponential moving average"],

    # -------- PRICE / VOLUME --------
    "PRICE": ["price", "stock price", "closing price", "close price"],
    "VOLUME": ["volume", "trading volume"]
}

# =========================================================
# CANONICAL INDICATORS (AFTER NORMALIZATION)
# =========================================================
INDICATORS = {
    "PRICE": {},
    "VOLUME": {},
    "RSI": {},
    "MACD": {},
    "ADX": {},

    "SMA": {"period": True},
    "EMA": {"period": True},

    "PE": {},
    "PB": {},
    "PS": {},
    "PEG": {},
    "MARKET_CAP": {},

    "ROE": {},
    "ROA": {},
    "ROCE": {},

    "DEBT_EQUITY": {},
    "CURRENT_RATIO": {},
    "QUICK_RATIO": {},

    "DIVIDEND_YIELD": {}
}

# =========================================================
# UTILITIES
# =========================================================
def error(msg):
    return {"error": msg}

def normalize_text(text):
    text = text.lower()
    for canonical, variants in ALIASES.items():
        for v in variants:
            if v in text:
                text = text.replace(v, canonical.lower())
    return text

def extract_operator(text):
    for k, v in OPERATOR_MAP.items():
        if k in text:
            return k, v
    return None, None

def extract_number(text):
    nums = re.findall(r"\d+\.?\d*", text)
    return float(nums[0]) if nums else None

def extract_indicator(text):
    text = text.upper()

    for ind, cfg in INDICATORS.items():
        if cfg.get("period"):
            match = re.search(rf"{ind}\s*(\d+)", text)
            if match:
                return {"type": ind, "period": int(match.group(1))}
        else:
            if ind in text:
                return {"type": ind}

    return None

# =========================================================
# PARSER
# =========================================================
def parse_condition(text):
    op_text, operator = extract_operator(text)
    if not operator:
        return error(f"Operator missing or invalid in: '{text}'")

    left = extract_indicator(text)
    if not left:
        return error(f"Indicator missing or invalid in: '{text}'")

    remaining = text.replace(op_text, "")
    right_indicator = extract_indicator(remaining)
    number = extract_number(remaining)

    if operator in ["CROSS_ABOVE", "CROSS_BELOW"]:
        if not right_indicator:
            return error("Crossover requires two indicators")
        return {
            "left": left,
            "operator": operator,
            "right": right_indicator
        }

    if number is not None:
        return {
            "left": left,
            "operator": operator,
            "right": number
        }

    if right_indicator:
        return {
            "left": left,
            "operator": operator,
            "right": right_indicator
        }

    return error(f"Right-hand value missing in: '{text}'")

# =========================================================
# MAIN DSL GENERATOR
# =========================================================
def generate_dsl(user_input):
    """
    Convert natural language stock screening queries to DSL format.
    
    Args:
        user_input: Natural language query (e.g., "pe below 20 and roe above 15")
        
    Returns:
        Dictionary with status and conditions, or error message
        
    Examples:
        >>> generate_dsl("pe below 20")
        {'status': 'success', 'conditions': [{'left': {'type': 'PE'}, 'operator': '<', 'right': 20.0}]}
    """
    if not user_input or len(user_input.strip()) < 3:
        return error("Input text empty or invalid")

    user_input = normalize_text(user_input)
    parts = user_input.split(" and ")
    conditions = []

    for part in parts:
        parsed = parse_condition(part)
        if "error" in parsed:
            return parsed
        conditions.append(parsed)

    return {
        "status": "success",
        "conditions": conditions
    }


# Legacy function for backward compatibility
def parse_dsl(text: str) -> dict:
    """
    Legacy DSL parser - kept for backward compatibility.
    Use generate_dsl() instead for enhanced functionality.
    """
    filters = {}

    pe_match = re.search(r"pe\s*<\s*(\d+)", text, re.I)
    if pe_match:
        filters["pe_ratio"] = {"lt": int(pe_match.group(1))}

    mc_match = re.search(r"market cap\s*>\s*(\d+)", text, re.I)
    if mc_match:
        filters["market_cap"] = {"gt": int(mc_match.group(1)) * 10_000_000}

    return filters
