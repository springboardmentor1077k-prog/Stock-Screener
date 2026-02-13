import requests
import time
import subprocess
import os
import signal

def test_fastapi_resilience():
    base_url = "http://127.0.0.1:8001"
    
    # Check if server is already running
    try:
        requests.get(f"{base_url}/health")
        print("Using existing server on port 8001")
        server_process = None
    except:
        print("Starting new server on port 8001")
        server_process = subprocess.Popen(
            ["uvicorn", "Stock-Screener.fastapi_backend.main:app", "--port", "8001", "--host", "127.0.0.1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)
    
    print("\n--- Testing FastAPI Resilience ---")
    
    # 1. Test Health Check
    try:
        resp = requests.get(f"{base_url}/health")
        print(f"Health Check: {resp.status_code} | {resp.json()}")
    except Exception as e:
        print(f"Health Check Failed: {e}")

    # 2. Test Validation Error (Invalid Symbol)
    payload = {"symbol": "INVALID_SYM", "condition": "Above Price", "value": 100.0}
    resp = requests.post(f"{base_url}/alerts", json=payload)
    print(f"Validation Error (Symbol): {resp.status_code} | {resp.json()}")

    # 3. Test Compliance Error (Predictive Query)
    payload = {"query": "show future growth stocks", "sector": "All", "strong_only": False, "market_cap": "Any"}
    resp = requests.post(f"{base_url}/screen", json=payload)
    print(f"Compliance Error: {resp.status_code} | {resp.json()}")

    # 4. Test Duplicate Alert Protection
    payload = {"symbol": "AAPL", "condition": "Above Price", "value": 150.0}
    # First creation
    requests.post(f"{base_url}/alerts", json=payload)
    # Second creation (duplicate)
    resp = requests.post(f"{base_url}/alerts", json=payload)
    print(f"Duplicate Alert: {resp.status_code} | {resp.json()}")

    # 5. Test Global Error Sanitization (Force an error with secret query)
    resp = requests.post(f"{base_url}/screen", json={"query": "TRIGGER_500_ERROR"})
    print(f"Error Sanitization (500): {resp.status_code} | {resp.json()}")

    # 6. Test Resource Not Found (404)
    resp = requests.get(f"{base_url}/non-existent-endpoint")
    print(f"Not Found (404): {resp.status_code} | {resp.json()}")

    # 7. Test Validation Error with Details
    resp = requests.post(f"{base_url}/screen", json={"query": ""})
    print(f"Validation Error (Empty Query): {resp.status_code} | {resp.json()}")

    # Terminate server if we started it
    if server_process:
        server_process.terminate()
    print("\n--- Resilience Testing Complete ---")

if __name__ == "__main__":
    test_fastapi_resilience()
