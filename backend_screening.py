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
# Fallback to env var if needed, but hardcoding as per previous file state
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-3.5-turbo"

# ===============================
# DSL RULES
# ===============================
ALLOWED_FIELDS = {"pe_ratio", "peg_ratio", "sector", "net_profit", "revenue", "ebitda"}
SNAPSHOT_FIELDS = {"pe_ratio", "peg_ratio", "sector"}
TIME_SERIES_FIELDS = {"net_profit", "revenue", "ebitda"}
ALLOWED_OPERATORS = {"<", "=", ">"}

# ===============================
# DB CONNECTION
# ===============================
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ===============================
# DSL VALIDATION (RECURSIVE)
# ===============================
def validate_node(node: dict, path: str = "root"):
    # 1. Logical Node
    if "logic" in node:
        if node["logic"] not in {"AND", "OR"}:
            raise ValueError(f"Invalid logic at {path}: {node['logic']}")
        
        if "conditions" not in node or not isinstance(node["conditions"], list):
            raise ValueError(f"Logical node at {path} must have 'conditions' list")
            
        if "field" in node:
            raise ValueError(f"Logical node at {path} cannot have 'field'")
            
        for i, child in enumerate(node["conditions"]):
            validate_node(child, path=f"{path}.conditions[{i}]")

    # 2. Condition Node
    elif "field" in node:
        if "logic" in node:
            raise ValueError(f"Condition node at {path} cannot have 'logic'")
            
        field = node["field"]
        if field not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field at {path}: {field}")
            
        if node["operator"] not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator at {path}: {node['operator']}")
            
        if "value" not in node:
            raise ValueError(f"Missing value at {path}")

        # Time-series validation
        if field in TIME_SERIES_FIELDS:
            if "time_window" not in node:
               raise ValueError(f"Missing time_window for time-series field at {path}: {field}")
            
            tw = node["time_window"]
            if tw.get("type") != "last_n_quarters":
                raise ValueError(f"time_window type must be 'last_n_quarters' at {path}")
            
            if not isinstance(tw.get("value"), int) or tw["value"] <= 0:
                 raise ValueError(f"time_window value must be a positive integer at {path}")
    
    # 3. Invalid Node
    else:
        raise ValueError(f"Node at {path} must have either 'logic' or 'field'")

def validate_dsl(dsl: dict):
    print("🧪 Validating DSL (Recursive)...")
    # Normalize old "flat list" format if present
    if "filters" in dsl and "logic" not in dsl:
        print("   ⚠️ Legacy 'filters' detected, treating as implicit AND")
        dsl = {"logic": "AND", "conditions": dsl["filters"]}
    
    validate_node(dsl)
    print("✅ DSL validation passed")
    return dsl

# ===============================
# RECURSIVE SQL COMPILER
# ===============================
def compile_dsl(node: dict) -> tuple:
    # Returns (sql_string, params_list)
    
    # 1. LOGICAL NODE
    if "logic" in node:
        operator = node["logic"] # AND / OR
        child_sqls = []
        child_params = []
        
        if not node.get("conditions"):
             # Empty logic node -> True for AND, False for OR
             return ("1=1" if operator == "AND" else "1=0"), []
             
        for child in node["conditions"]:
            c_sql, c_params = compile_dsl(child)
            child_sqls.append(f"({c_sql})")
            child_params.extend(c_params)
            
        # Join with the logical operator
        full_sql = f" {operator} ".join(child_sqls)
        return full_sql, child_params

    # 2. CONDITION NODE
    else:
        field = node["field"]
        op = node["operator"]
        value = node["value"]
        
        # A. Snapshot Fields
        if field in SNAPSHOT_FIELDS:
            # Map field to table alias
            # sm -> stock_metrics, st -> stock_master
            prefix = "st" if field == "sector" else "sm"
            return f"{prefix}.{field} {op} %s", [value]
            
        # B. Time-Series Fields
        elif field in TIME_SERIES_FIELDS:
            limit_n = node["time_window"]["value"]
            
            subquery = f"""
                EXISTS (
                    SELECT 1
                    FROM quarterly_financials q
                    WHERE q.stock_id = st.stock_id
                      AND q.{field} {op} %s
                    ORDER BY q.financial_year DESC, q.quarter DESC
                    LIMIT %s
                )
            """
            return subquery.strip(), [value, limit_n]
            
    raise ValueError("Unknown node type during compilation")

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
- Allowed snapshot fields: pe_ratio, peg_ratio, sector
- Allowed time-series fields: net_profit, revenue, ebitda
- Allowed operators: <, =, >
- For time-series fields, INCLUDE "time_window": {{ "type": "last_n_quarters", "value": N }}

Structure:
- The root object must have "logic" ("AND" or "OR") and "conditions" (list).
- You can nest "logic" nodes inside "conditions" to create complex queries.
- A "condition" node has "field", "operator", "value" (and "time_window" if needed).

Example 1 (Simple):
{{
  "logic": "AND",
  "conditions": [
    {{ "field": "pe_ratio", "operator": "<", "value": 20 }},
    {{ "field": "sector", "operator": "=", "value": "IT" }}
  ]
}}

Example 2 (Nested):
{{
  "logic": "AND",
  "conditions": [
    {{
      "logic": "OR",
      "conditions": [
        {{ "field": "pe_ratio", "operator": "<", "value": 15 }},
        {{ "field": "peg_ratio", "operator": "<", "value": 1 }}
      ]
    }},
    {{
      "field": "net_profit",
      "operator": ">",
      "value": 1000,
      "time_window": {{ "type": "last_n_quarters", "value": 1 }}
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

        # 3️⃣ DSL Validation (Normalizes to Nested Structure)
        dsl = validate_dsl(dsl)

        # 4️⃣ Compile DSL → SQL (Recursive)
        print("\n🧱 Compiling DSL to SQL...")
        
        where_clause, values = compile_dsl(dsl)

        if not where_clause:
            raise ValueError("No valid conditions")

        sql = f"""
            SELECT
                st.symbol,
                st.company_name,
                sm.pe_ratio
            FROM stock_master st
            JOIN stock_metrics sm
                ON st.stock_id = sm.stock_id
            WHERE {where_clause}
        """

        print("🧾 SQL QUERY:")
        print(sql)
        print("🔢 SQL VALUES:", values)

        # 5️⃣ Execute SQL
        print("\n💾 Executing SQL...")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, tuple(values))
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
