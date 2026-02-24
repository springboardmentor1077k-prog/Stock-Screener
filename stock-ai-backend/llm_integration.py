import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL = "mistral"


SYSTEM_PROMPT = """
You are a STRICT JSON DSL generator for a stock screening system.

Your job is to convert a user’s natural language query into a JSON-based DSL.

You MUST follow these rules exactly.

----------------------------------
SUPPORTED QUERY TYPE
----------------------------------
Only STOCK FILTERING queries are supported.

If the query is NOT a filtering query
(e.g. prediction, recommendation, future performance),
output EXACTLY:

{"invalid": true}

----------------------------------
DSL STRUCTURE
----------------------------------

The DSL is a TREE made of nodes.

There are ONLY two node types:

1) CONDITION NODE
2) LOGICAL NODE

----------------------------------
1) CONDITION NODE
----------------------------------
Represents ONE rule on ONE database field.

Structure:
{
  "type": "condition",
  "field": "<exact database field name>",
  "operator": "< | > | = | <= | >=",
  "value": "<number or string>",
  "last_n": <number> (OPTIONAL, ONLY for quarterly fields)
}

Rules:
- Each condition checks ONLY ONE field
- Do NOT combine multiple fields in one condition
- "last_n" is allowed ONLY for quarterly fields

----------------------------------
2) LOGICAL NODE
----------------------------------
Combines conditions using AND / OR.

Structure:
{
  "type": "logical",
  "operator": "AND | OR",
  "children": [ <node>, <node>, ... ]
}

Rules:
- A logical node MUST have at least 2 children
- Children can be condition nodes OR logical nodes
- Nesting is allowed

----------------------------------
ALLOWED DATABASE FIELDS
----------------------------------

Use ONLY the following exact field names:

Snapshot fields:
- company_name
- sector
- exchange
- fundamentals.pe_ratio
- fundamentals.peg_ratio
- fundamentals.debt
- fundamentals.free_cash_flow
- analyst_targets.target_price_low
- analyst_targets.target_price_high
- analyst_targets.current_market_price

Quarterly (time-series) fields:
- quarterly_financials.revenue
- quarterly_financials.ebitda
- quarterly_financials.net_profit

----------------------------------
OPERATOR RULES
----------------------------------
Allowed operators:
<  >  =  <=  >=

----------------------------------
OUTPUT RULES (STRICT)
----------------------------------
- Output ONLY valid JSON
- JSON MUST start with { and end with }
- NO explanations
- NO markdown
- NO comments
- NO extra keys

----------------------------------
EXAMPLES
----------------------------------

Input:
Show technology stocks with PE ratio less than 25

Output:
{
  "type": "logical",
  "operator": "AND",
  "children": [
    {
      "type": "condition",
      "field": "sector",
      "operator": "=",
      "value": "Technology"
    },
    {
      "type": "condition",
      "field": "fundamentals.pe_ratio",
      "operator": "<",
      "value": 25
    }
  ]
}

----------------------------------

Input:
PE ratio less than 10 AND net profit positive for last 4 quarters

Output:
{
  "type": "logical",
  "operator": "AND",
  "children": [
    {
      "type": "condition",
      "field": "fundamentals.pe_ratio",
      "operator": "<",
      "value": 10
    },
    {
      "type": "condition",
      "field": "quarterly_financials.net_profit",
      "operator": ">",
      "value": 0,
      "last_n": 4
    }
  ]
}

----------------------------------

Input:
Predict next quarter performance

Output:
{"invalid": true}

"""


def english_to_dsl(query: str):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
        "temperature": 0
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        # OpenAI-compatible response parsing
        content = data["choices"][0]["message"]["content"].strip()
        
        # Extract JSON from response (handles markdown code fences and plain JSON)
        json_str = None
        
        # Case 1: Content has markdown code fences (```json ... ```)
        if "```" in content:
            # Extract content between code fences
            # Find ```json or ``` followed by the JSON
            start_marker = content.find("```")
            if start_marker != -1:
                # Skip past the ``` and optional language identifier
                start_content = content[start_marker + 3:]
                # Skip to next line if there's a language identifier
                if start_content.startswith("json"):
                    start_content = start_content[4:]
                start_content = start_content.lstrip()
                
                # Find the closing ```
                end_marker = start_content.find("```")
                if end_marker != -1:
                    json_str = start_content[:end_marker].strip()
        
        # Case 2: Try to find JSON directly by looking for { ... }
        if not json_str:
            start_idx = content.find("{")
            end_idx = content.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx+1]
        
        if json_str:
            # Strip JavaScript-style comments (// ...) before parsing
            import re
            # Remove single-line comments
            json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
            # Remove multi-line comments
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
            
            parsed = json.loads(json_str)
            if parsed.get("invalid") is True:
                fallback = _fallback_dsl_for_quarterly_signals(query)
                if fallback:
                    return fallback
            return parsed
        else:
            fallback = _fallback_dsl_for_quarterly_signals(query)
            return fallback or {"invalid": True}

    except requests.exceptions.RequestException as e:
        print(f"Ollama Connection Error: {e}")
        return {"invalid": True}

    except json.JSONDecodeError as e:
        print(f"LLM returned non-JSON output: {e}")
        fallback = _fallback_dsl_for_quarterly_signals(query)
        return fallback or {"invalid": True}

    except Exception as e:
        print(f"Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        fallback = _fallback_dsl_for_quarterly_signals(query)
        return fallback or {"invalid": True}


def _fallback_dsl_for_quarterly_signals(query: str):
    """
    Deterministic fallback for common quarterly filter intents when LLM output is invalid.

    Supported examples:
    - "Stocks with positive profit in last 2 quarters"
    - "Stocks with positive net profit for last 4 quarters"
    - "negative ebitda in last 3 quarters"
    """
    if not query:
        return None

    q = query.lower().strip()

    last_n_match = re.search(r"(?:in|for)\s+last\s+(\d+)\s+quarters?", q)
    if not last_n_match:
        return None

    last_n = int(last_n_match.group(1))
    if last_n <= 0:
        return None

    if "net profit" in q or re.search(r"\bprofit\b", q):
        field = "quarterly_financials.net_profit"
    elif "ebitda" in q:
        field = "quarterly_financials.ebitda"
    elif "revenue" in q:
        field = "quarterly_financials.revenue"
    else:
        return None

    if "positive" in q:
        operator, value = ">", 0
    elif "negative" in q or "loss" in q:
        operator, value = "<", 0
    else:
        return None

    return {
        "type": "condition",
        "field": field,
        "operator": operator,
        "value": value,
        "last_n": last_n
    }
