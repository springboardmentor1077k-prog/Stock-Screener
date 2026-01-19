import os
import json
import re
import requests

SCHEMA = {
    "type": "object",
    "properties": {
        "industry_category": {"type": "string"},
        "filters": {
            "type": "object",
            "properties": {
                "peg_ratio_max": {"type": "number"},
                "fcf_to_debt_min": {"type": "number"},
                "price_vs_target": {"type": "string"},
                "revenue_yoy_positive": {"type": "boolean"},
                "ebitda_yoy_positive": {"type": "boolean"},
                "earnings_beat_likely": {"type": "boolean"},
                "buyback_announced": {"type": "boolean"},
                "next_earnings_within_days": {"type": "integer"}
            },
            "required": [
                "peg_ratio_max",
                "fcf_to_debt_min",
                "price_vs_target",
                "revenue_yoy_positive",
                "ebitda_yoy_positive",
                "earnings_beat_likely",
                "buyback_announced",
                "next_earnings_within_days"
            ]
        }
    },
    "required": ["industry_category", "filters"]
}

def build_system_prompt():
    return (
        "You output only JSON that strictly conforms to the provided schema. "
        "No explanations, no markdown, no code fences, no extra fields. "
        "If the query is incomplete, infer conservative defaults. Schema: "
        + json.dumps(SCHEMA)
    )

def local_parse(query: str) -> dict:
    text = query.lower()
    industry_category = "Information Technology"
    peg_ratio_max = 3.0
    fcf_to_debt_min = 0.25
    price_vs_target = "<= target_low"
    revenue_yoy_positive = True
    ebitda_yoy_positive = True
    earnings_beat_likely = True
    buyback_announced = True
    next_earnings_within_days = 30
    m = re.search(r"peg[^\d]*([\d\.]+)", text)
    if m:
        try:
            peg_ratio_max = float(m.group(1))
        except Exception:
            pass
    m = re.search(r"debt[^\d]*([\d\.]+)\s*%|debt[^\d]*([\d\.]+)\s*ratio", text)
    if m:
        for g in m.groups():
            if g:
                try:
                    v = float(g)
                    fcf_to_debt_min = v if v <= 1 else v / 100.0
                except Exception:
                    pass
                break
    m = re.search(r"earnings[^\d]*(\d{1,3})\s*day", text)
    if m:
        try:
            next_earnings_within_days = int(m.group(1))
        except Exception:
            pass
    if "buyback" in text or "buy back" in text:
        buyback_announced = True
    if "likely" in text or "beat" in text:
        earnings_beat_likely = True
    if any(k in text for k in ["telecom", "semiconductor", "software", "hardware", "it"]):
        industry_category = "Information Technology"
    return {
        "industry_category": industry_category,
        "filters": {
            "peg_ratio_max": peg_ratio_max,
            "fcf_to_debt_min": fcf_to_debt_min,
            "price_vs_target": price_vs_target,
            "revenue_yoy_positive": revenue_yoy_positive,
            "ebitda_yoy_positive": ebitda_yoy_positive,
            "earnings_beat_likely": earnings_beat_likely,
            "buyback_announced": buyback_announced,
            "next_earnings_within_days": next_earnings_within_days
        }
    }

def openai_parse(query: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return local_parse(query)
    url = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": query}
        ],
        "temperature": 0
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        return local_parse(query)

def generate_dsl(query: str, provider: str = "local") -> dict:
    if provider.lower() == "openai":
        return openai_parse(query)
    return local_parse(query)

def save_json(obj: dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)