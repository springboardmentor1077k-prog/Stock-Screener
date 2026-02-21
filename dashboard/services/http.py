import requests


BASE_URL = "http://127.0.0.1:5000/api/v2"
AUTH_TOKEN = None


class NetworkError(Exception):
    pass


def set_token(token: str | None):
    global AUTH_TOKEN
    AUTH_TOKEN = token


def _do(method, path, json=None, params=None, timeout=10):
    url = f"{BASE_URL}{path}"
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    try:
        resp = requests.request(method, url, json=json, params=params, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        raise NetworkError(str(e))
    ct = resp.headers.get("content-type", "")
    if "application/json" not in ct:
        raise NetworkError(f"unexpected content type: {ct}")
    data = resp.json()
    return data, resp.status_code


def parse_response(data, status_code):
    if status_code >= 400:
        code = data.get("code") if isinstance(data, dict) else "http_error"
        msg = data.get("message") if isinstance(data, dict) else "request failed"
        raise NetworkError(f"{code}: {msg}")
    if not isinstance(data, dict):
        raise NetworkError("invalid response")
    if not data.get("ok"):
        raise NetworkError(f"{data.get('code','unknown')}: {data.get('message','error')}")
    items = data.get("items", [])
    return items, data.get("count", len(items))


def get(path, params=None):
    data, status = _do("GET", path, params=params)
    return parse_response(data, status)


def post(path, payload=None):
    data, status = _do("POST", path, json=payload)
    return parse_response(data, status)
