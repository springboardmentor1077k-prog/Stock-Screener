import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.api_server import app
import json


def run():
    c = app.test_client()
    # register/login to get token
    c.post("/api/v2/register", json={"email": "smoke@example.com", "password": "secret12"})
    lr = c.post("/api/v2/login", json={"email": "smoke@example.com", "password": "secret12"})
    token = lr.get_json()["items"][0]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = c.post("/api/v2/screener", json={"query": "technology market cap above 100"}, headers=headers)
    assert r.status_code == 200, r.data
    d = r.get_json()
    assert d.get("ok") is True
    r2 = c.get("/api/v2/holdings", headers=headers)
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert d2.get("ok") is True
    r3 = c.get("/api/v2/alerts", headers=headers)
    assert r3.status_code == 200
    d3 = r3.get_json()
    assert d3.get("ok") is True
    print("OK")


if __name__ == "__main__":
    run()
