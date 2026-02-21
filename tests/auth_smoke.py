import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.api_server import app
import json
import time


def run():
    c = app.test_client()
    email = f"user{int(time.time())}@example.com"
    r = c.post("/api/v2/register", json={"email": email, "password": "secret12"})
    assert r.status_code in (200, 409), r.data
    if r.status_code == 200:
        d = r.get_json()
        assert d.get("ok") is True
    r2 = c.post("/api/v2/login", json={"email": email, "password": "secret12"})
    assert r2.status_code == 200, r2.data
    d2 = r2.get_json()
    assert d2.get("ok") is True
    items = d2.get("items", [])
    assert items and items[0].get("token")
    print("AUTH OK")


if __name__ == "__main__":
    run()

