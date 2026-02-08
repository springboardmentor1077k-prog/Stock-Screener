import requests
import json

API_URL = "http://localhost:8000/api/v1"

def run_test():
    print("🚀 Starting Screener Verification...")
    
    # 1. Login
    email = "verify@example.com"
    password = "password123"
    
    # Try signup (ignore if exists)
    requests.post(f"{API_URL}/auth/signup", json={"email": email, "password": password})
    
    # Login
    login_res = requests.post(f"{API_URL}/auth/login", data={"username": email, "password": password})
    
    if login_res.status_code != 200:
        print(f"❌ Login failed: {login_res.text}")
        return
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in successfully")
    
    # 2. Execute Screen Query
    # We want any stock, so just execute a global search or a broad condition
    # Let's try global search for "TCS" or just empty conditions which returns all (limited by DB fetch usually, but here no limit on fetch_all?)
    # Fetch all might be dangerous if many stocks, but we have few.
    
    payload = {
        "action": "screen",
        "conditions": [],
        "global_search": "TCS" # Search for TCS specifically
    }
    
    print(f"🔍 Searching for: {payload}")
    res = requests.post(f"{API_URL}/screener/search", json=payload, headers=headers)
    
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Search successful. Found {len(data)} results.")
        
        for stock in data:
            print(f"  - {stock['symbol']}: {stock.get('fundamentals')}")
            if stock.get('fundamentals'):
                 print(f"    -> PE: {stock['fundamentals'].get('pe_ratio')}")
                 print(f"    -> Price: {stock['fundamentals'].get('current_price')}")
            else:
                 print("    ❌ FUNDAMENTALS MISSING")
                 
    else:
        print(f"❌ Search failed: {res.status_code} {res.text}")

if __name__ == "__main__":
    run_test()
