import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

PROMPT = """
You are a STRICT financial query parser that converts natural language to JSON DSL.

CRITICAL RULES:
1. ONLY support these exact fields: pe_ratio, net_profit
2. ONLY support these operators: >, >=, <, <=, =
3. REJECT queries asking for:
   - Future data (forward PE, future profits, predictions)
   - Guaranteed/certain outcomes
   - Data we don't have (revenue, growth rates, etc.)
4. For quarterly conditions, only support "positive net profit for last N quarters"

If the query asks for unsupported data or concepts, return:
{"error": "UNSUPPORTED_QUERY", "message": "This query asks for data we don't have. Try: 'PE ratio > 15' or 'positive profit last 4 quarters'"}

Valid example: "PE ratio > 5 and positive profit last 4 quarters"
Invalid examples: "future PE ratio", "guaranteed profit", "revenue growth"

Output ONLY valid JSON, no explanations.

Valid format:
{
  "conditions": [
    { "field": "pe_ratio", "operator": ">=", "value": 5 },
    { "field": "net_profit", "type": "quarterly", "condition": "positive", "last_n": 4 }
  ],
  "logic": "AND"
}
"""

def parse_query_to_dsl(query: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            dsl = json.loads(content)
            
            if "error" in dsl:
                if dsl.get("error") == "UNSUPPORTED_QUERY":
                    raise ValueError(dsl.get("message", "This query asks for data we don't have"))
                else:
                    raise ValueError(dsl.get("error", "Invalid query"))
                
            return dsl
        except json.JSONDecodeError:
            raise ValueError(f"Invalid query - could not parse: {query}")
            
    except Exception as e:
        raise ValueError(f"Invalid query: {str(e)}")
