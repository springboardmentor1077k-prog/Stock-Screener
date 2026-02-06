from fastapi import FastAPI, HTTPException
import psycopg2
import requests
import os
import json
import re

app = FastAPI()

# ===============================
# DATABASE CONFIG
# ===============================
DB_CONFIG = {
    "dbname": "stocks_db",
    "user": "postgres",
    "password": "Nethra@02",
    "host": "localhost",
    "port": 5432
}

# ===============================
# OPENROUTER CONFIG
# ===============================
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-3.5-turbo"

# ===============================
# DSL RULES
# ===============================
ALLOWED_FIELDS = {"pe_ratio", "sector"}
ALLOWED_OPERATORS = {"<", "=", ">"}

# ===============================
# DB CONNECTION
# ===============================
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ===============================
# DSL VALIDATION
# ===============================
def validate_dsl(dsl: dict):
    print("🧪 Validating DSL...")

    if "filters" not in dsl or not isinstance(dsl["filters"], list):
        raise ValueError("filters must be a list")

    for f in dsl["filters"]:
        print("   ↳ Filter:", f)

        if f["field"] not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field: {f['field']}")

        if f["operator"] not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator: {f['operator']}")

        if "value" not in f:
            raise ValueError("Missing value in filter")

    print("✅ DSL validation passed")

# ===============================
# LLM → DSL (DEBUG)
# ===============================
def nl_to_dsl(nl_query: str) -> dict:
    print("\n🔹 STEP 2: Calling LLM")
    print("Natural Language Query:", nl_query)

    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key not configured")

    prompt = f"""
Convert the following English stock screening query into STRICT JSON DSL.
Rules:
- Output ONLY valid JSON
- Allowed fields: pe_ratio, sector
- Allowed operators: <, =, >

JSON format:
{{
  "filters": [
    {{ "field": "...", "operator": "...", "value": ... }}
  ]
}}

English query:
{nl_query}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON. No text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
    response.raise_for_status()

    raw_content = response.json()["choices"][0]["message"]["content"]

    print("\n🧠 RAW LLM OUTPUT:")
    print(raw_content)

    match = re.search(r"\{.*\}", raw_content, re.DOTALL)
    if not match:
        raise ValueError("LLM did not return valid JSON")

    dsl = json.loads(match.group())

    print("\n📦 EXTRACTED DSL:")
    print(json.dumps(dsl, indent=2))

    return dsl

# ===============================
# SCREENER API
# ===============================
@app.post("/screen")
def screen_stocks(payload: dict):
    print("\n==============================")
    print("🚀 NEW REQUEST RECEIVED")
    print("Payload:", payload)

    try:
        # 1️⃣ Input
        if "query" not in payload:
            raise ValueError("Missing 'query' in request")

        # 2️⃣ NL → DSL
        dsl = nl_to_dsl(payload["query"])

        # 3️⃣ DSL Validation
        validate_dsl(dsl)

        # 4️⃣ Compile DSL → SQL
        print("\n🧱 Compiling DSL to SQL...")
        conditions = []
        values = []

        for f in dsl["filters"]:
            if f["field"] == "pe_ratio":
                conditions.append("sm.pe_ratio < %s")
                values.append(f["value"])

            elif f["field"] == "sector":
                conditions.append("st.sector = %s")
                values.append(f["value"])

        if not conditions:
            raise ValueError("No valid conditions")

        sql = f"""
            SELECT
                st.symbol,
                st.company_name,
                sm.pe_ratio
            FROM stock_master st
            JOIN stock_metrics sm
                ON st.stock_id = sm.stock_id
            WHERE {" AND ".join(conditions)}
        """

        print("🧾 SQL QUERY:")
        print(sql)
        print("🔢 SQL VALUES:", values)

        # 5️⃣ Execute SQL
        print("\n💾 Executing SQL...")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, values)
        rows = cur.fetchall()
        conn.close()

        print(f"✅ Rows fetched: {len(rows)}")

        return {
            "results": [
                {
                    "symbol": r[0],
                    "company_name": r[1],
                    "pe_ratio": float(r[2])
                } for r in rows
            ]
        }

    except ValueError as e:
        print("❌ VALIDATION ERROR:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print("🔥 INTERNAL ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
=======
from fastapi import FastAPI, HTTPException
import psycopg2
import requests
import os
import json
import re

app = FastAPI()

# ===============================
# DATABASE CONFIG
# ===============================
DB_CONFIG = {
    "dbname": "stocks_db",
    "user": "postgres",
    "password": "Nethra@02",
    "host": "localhost",
    "port": 5432
}

# ===============================
# OPENROUTER CONFIG
# ===============================
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-3.5-turbo"

# ===============================
# DSL RULES
# ===============================
ALLOWED_FIELDS = {"pe_ratio", "sector", "net_profit", "revenue", "ebitda"}
SNAPSHOT_FIELDS = {"pe_ratio", "sector"}
TIME_SERIES_FIELDS = {"net_profit", "revenue", "ebitda"}
ALLOWED_OPERATORS = {"<", "=", ">"}

# ===============================
# DB CONNECTION
# ===============================
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ===============================
# DSL VALIDATION
# ===============================
def validate_dsl(dsl: dict):
    print("🧪 Validating DSL...")

    if "filters" not in dsl or not isinstance(dsl["filters"], list):
        raise ValueError("filters must be a list")

    for f in dsl["filters"]:
        print("   ↳ Filter:", f)

        if f["field"] not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field: {f['field']}")

        if f["operator"] not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator: {f['operator']}")

        if "value" not in f:
            raise ValueError("Missing value in filter")

        # Time-series validation
        if f["field"] in TIME_SERIES_FIELDS:
            if "time_window" not in f:
               raise ValueError(f"Missing time_window for time-series field: {f['field']}")
            
            tw = f["time_window"]
            if tw.get("type") != "last_n_quarters":
                raise ValueError("time_window type must be 'last_n_quarters'")
            
            if not isinstance(tw.get("value"), int) or tw["value"] <= 0:
                 raise ValueError("time_window value must be a positive integer")

    print("✅ DSL validation passed")

# ===============================
# LLM → DSL (DEBUG)
# ===============================
def nl_to_dsl(nl_query: str) -> dict:
    print("\n🔹 STEP 2: Calling LLM")
    print("Natural Language Query:", nl_query)

    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key not configured")

    prompt = f"""
Convert the following English stock screening query into STRICT JSON DSL.
Rules:
- Output ONLY valid JSON
- Allowed snapshot fields: pe_ratio, sector
- Allowed time-series fields: net_profit, revenue, ebitda
- Allowed operators: <, =, >
- For time-series fields (net_profit, revenue, ebitda), you MUST include a "time_window" object
  with "type": "last_n_quarters" and "value": <number of quarters>.
  If the user says "last 4 quarters" or "past year", value is 4.
  If implied "current", value is 1.

JSON format:
{{
  "filters": [
    {{ 
      "field": "...", 
      "operator": "...", 
      "value": ...,
      "time_window": {{ "type": "last_n_quarters", "value": 4 }} // Optional for snapshot, REQUIRED for time-series
    }}
  ]
}}

English query:
{nl_query}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON. No text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
    response.raise_for_status()

    raw_content = response.json()["choices"][0]["message"]["content"]

    print("\n🧠 RAW LLM OUTPUT:")
    print(raw_content)

    match = re.search(r"\{.*\}", raw_content, re.DOTALL)
    if not match:
        raise ValueError("LLM did not return valid JSON")

    dsl = json.loads(match.group())

    print("\n📦 EXTRACTED DSL:")
    print(json.dumps(dsl, indent=2))

    return dsl

# ===============================
# SCREENER API
# ===============================
@app.post("/screen")
def screen_stocks(payload: dict):
    print("\n==============================")
    print("🚀 NEW REQUEST RECEIVED")
    print("Payload:", payload)

    try:
        # 1️⃣ Input
        if "query" not in payload:
            raise ValueError("Missing 'query' in request")

        # 2️⃣ NL → DSL
        dsl = nl_to_dsl(payload["query"])

        # 3️⃣ DSL Validation
        validate_dsl(dsl)

        # 4️⃣ Compile DSL → SQL
        print("\n🧱 Compiling DSL to SQL...")
        conditions = []
        values = []

        for f in dsl["filters"]:
            field = f["field"]
            operator = f["operator"]
            value = f["value"]

            # SNAPSHOT FIELDS (stock_metrics or stock_master)
            if field in SNAPSHOT_FIELDS:
                if field == "pe_ratio":
                    conditions.append(f"sm.pe_ratio {operator} %s")
                    values.append(value)
                elif field == "sector":
                    conditions.append(f"st.sector {operator} %s")
                    values.append(value)
            
            # TIME-SERIES FIELDS (quarterly_financials)
            elif field in TIME_SERIES_FIELDS:
                limit_n = f["time_window"]["value"]
                
                # Subquery construction
                # q.{field} needs to be safe. Since field is validated against whitelist, it's safe.
                subquery = f"""
                    EXISTS (
                        SELECT 1
                        FROM quarterly_financials q
                        WHERE q.stock_id = st.stock_id
                          AND q.{field} {operator} %s
                        ORDER BY q.financial_year DESC, q.quarter DESC
                        LIMIT %s
                    )
                """
                
                conditions.append(subquery.strip())
                values.append(value)   # Main condition value
                values.append(limit_n) # Limit value

        if not conditions:
            raise ValueError("No valid conditions")

        sql = f"""
            SELECT
                st.symbol,
                st.company_name,
                sm.pe_ratio
            FROM stock_master st
            JOIN stock_metrics sm
                ON st.stock_id = sm.stock_id
            WHERE {" AND ".join(conditions)}
        """

        print("🧾 SQL QUERY:")
        print(sql)
        print("🔢 SQL VALUES:", values)

        # 5️⃣ Execute SQL
        print("\n💾 Executing SQL...")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, values)
        rows = cur.fetchall()
        conn.close()

        print(f"✅ Rows fetched: {len(rows)}")

        return {
            "results": [
                {
                    "symbol": r[0],
                    "company_name": r[1],
                    "pe_ratio": float(r[2]) if r[2] else 0.0
                } for r in rows
            ]
        }

    except ValueError as e:
        print("❌ VALIDATION ERROR:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print("🔥 INTERNAL ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

