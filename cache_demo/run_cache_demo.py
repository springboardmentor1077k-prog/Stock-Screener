import time
import json
import requests

BASE = "http://127.0.0.1:5000"
payload = {
    "query": "Show IT sector stocks",
    "sector": "All",
    "strong_only": False,
    "market_cap": "Any",
}

def call():
    t0 = time.time()
    r = requests.post(f"{BASE}/screen", json=payload, timeout=15)
    dt = int((time.time() - t0) * 1000)
    j = r.json()
    print(f"HTTP {r.status_code} | cached={j.get('cached')} | latency_ms={j.get('latency_ms')} | measured_ms={dt}")
    return j

def main():
    print("=== Cache Demo: First call (expect MISS) ===")
    j1 = call()
    print("=== Cache Demo: Second call (expect HIT) ===")
    j2 = call()
    if j1.get("cached") is False and j2.get("cached") is True:
        print("OK: Hit/Miss behavior verified")
    else:
        print("WARN: Unexpected caching flags", j1.get("cached"), j2.get("cached"))

if __name__ == "__main__":
    main()
