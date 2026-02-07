import requests
import json

API_URL = "http://127.0.0.1:8000/screen"

def test_query(name, payload):
    print(f"\n--- Testing {name} ---")
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        print("Status: Success")
        print(f"Results count: {len(data.get('results', []))}")
        # print("Results:", json.dumps(data, indent=2))
    except Exception as e:
        print(f"Status: Failed - {e}")
        if hasattr(e, 'response') and e.response:
            print("Response:", e.response.text)

# 1. Simple Flat Query (Legacy Support)
test_query("Legacy Flat Query", {
    "query": "Show me stocks with PE ratio less than 20"
})

# 2. Nested Logic Query
# Logic: (PE < 20 OR Sector = 'IT') AND Net Profit > 0 (Last 4 quarters)
# Note: Since we are mocking the LLM part in a real test we'd need to mock nl_to_dsl, 
# but here we are calling the API which calls the LLM. 
# To test the DSL compiler directly, we might need a different approach if we don't want to spend API credits or rely on LLM determinism.
# However, the user wants to see the system work.
test_query("Nested Logic (Natural Language)", {
    "query": "Show me stocks with PE ratio less than 25 OR sector is IT, AND net profit is positive for the last 4 quarters"
})
