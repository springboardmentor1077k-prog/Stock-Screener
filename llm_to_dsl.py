import openai
import json
import re

# ==============================
# Configure Your API Key
# ==============================
openai.api_key = "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"

# ==============================
# Strict Prompt Template
# ==============================
STRICT_PROMPT = """
Convert the English stock screening query into a DSL JSON.
Rules:
1) Only output valid JSON — no extra text.
2) Use exactly these fields:
   - pe_ratio, peg_ratio, net_profit, revenue, sector
3) Allowed operators: <, >, =, growth_positive
4) Time window format:
   {
     "type": "last_n_quarters",
     "value": number
   }

Output JSON format:
{
  "filters": [
    {
      "field": string,
      "operator": string,
      "value": number or string,
      "time_window": { "type": "last_n_quarters", "value": number } (optional)
    }
  ],
  "logic": "AND" (optional if multiple filters)
}

English query:
"""

# ==============================
# Function to Call LLM
# ==============================
def call_real_llm(english_query: str):
    prompt = STRICT_PROMPT + english_query
    
    response = openai.ChatCompletion.create(
        model="gpt-4.4",       # or "gpt-3.5-turbo" if you don't have access
        messages=[
            {"role": "system", "content": "You are a DSL JSON generator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,  # deterministic output
        max_tokens=300
    )

    raw_output = response.choices[0].message["content"]
    print("Raw LLM Output:")
    print(raw_output)
    return raw_output

# ==============================
# Simple JSON Extractor
# ==============================
def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in LLM output")
    return json.loads(match.group())

# ==============================
# DSL Validation
# ==============================
ALLOWED_FIELDS = {"pe_ratio", "peg_ratio", "net_profit", "revenue", "sector"}
ALLOWED_OPERATORS = {"<", ">", "=", "growth_positive"}

def validate_dsl(dsl: dict) -> bool:
    if "filters" not in dsl or not isinstance(dsl["filters"], list):
        return False

    for f in dsl["filters"]:
        if f["field"] not in ALLOWED_FIELDS:
            return False
        if f["operator"] not in ALLOWED_OPERATORS:
            return False
        if "time_window" in f:
            tw = f["time_window"]
            if tw.get("type") != "last_n_quarters":
                return False
            if not isinstance(tw.get("value"), int):
                return False

    return True

# ==============================
# Main Workflow
# ==============================
if __name__ == "__main__":
    query = "Show IT sector stocks with PE ratio below 15 and positive net profit for the last 4 quarters"
    
    llm_text = call_real_llm(query)
    dsl_json = extract_json(llm_text)
    
    print("\nExtracted JSON:")
    print(json.dumps(dsl_json, indent=4))
    
    if validate_dsl(dsl_json):
        print("\n✅ DSL is valid.")
    else:
        print("\n❌ DSL is invalid.")
