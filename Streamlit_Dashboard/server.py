from flask import Flask, request, jsonify
import sqlite3
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
tables_dir = os.path.join(project_root, "tables")
if tables_dir not in sys.path:
    sys.path.append(tables_dir)

try:
    from config import DB_PATH
except Exception:
    DB_PATH = os.path.join(project_root, "analyst_demo", "stocks.db")

db_path = os.path.abspath(DB_PATH)

from ai_service import AIBackend

app = Flask(__name__)
ai_backend = AIBackend()

def ensure_schema(conn):
    try:
        from stocks import get_schema as stocks_schema
        from portfolios import get_schema as portfolios_schema
        from portfolio_holdings import get_schema as holdings_schema
        from alerts import get_schema as alerts_schema
        from alert_events import get_schema as alert_events_schema
        from analyst_ratings import get_schema as ratings_schema
        conn.executescript(stocks_schema())
        conn.executescript(portfolios_schema())
        conn.executescript(holdings_schema())
        conn.executescript(alerts_schema())
        conn.executescript(alert_events_schema())
        conn.executescript(ratings_schema())
        conn.commit()
    except Exception:
        pass

def get_db_connection():
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn

@app.route('/screen', methods=['POST'])
def screen_stocks():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        sector = data.get('sector', 'All')
        strong_only = data.get('strong_only', False)
        market_cap_filter = data.get('market_cap', 'Any')

        # Check if it's a "Sentence Query" (Longer, natural language)
        # Simple heuristic: if it contains spaces and > 1 word, treat as NL unless it's just a name
        is_natural_language = len(query.split()) > 2 or any(k in query.lower() for k in ["show", "find", "where", "stocks", "sector", "price", "pe ratio"])

        if is_natural_language:
            # --- AI / Natural Language Processing Path ---
            print(f"Processing Natural Language Query: {query}")
            ai_result = ai_backend.process_query(query)
            
            if not ai_result["is_valid"]:
                 return jsonify({
                    "status": "error", 
                    "message": ai_result.get("error_message", "Invalid query") + ": " + ai_result.get("reason", "")
                })
            
            sql = ai_result["generated_sql"]
            params = [] # AI backend generates complete SQL with values embedded for now
            print(f"Generated SQL: {sql}")
            
        else:
            # --- Standard Filter Path ---
            sql = "SELECT * FROM stocks WHERE 1=1"
            params = []
            if query:
                # Handle numeric queries for Price or PE Ratio directly if user enters a number
                try:
                    numeric_val = float(query)
                    sql += " AND (price > ? OR pe_ratio < ?)"
                    params.extend([numeric_val, numeric_val])
                except ValueError:
                    # Text search
                    sql += " AND (symbol LIKE ? OR company_name LIKE ?)"
                    params.extend([f"%{query}%", f"%{query}%"])
            if sector and sector != "All":
                sql += " AND sector = ?"
                params.append(sector)
            if strong_only:
                sql += " AND pe_ratio < 30 AND price > 20"
            # 4. Market Cap Filter
            if market_cap_filter == "Large Cap (>10B)":
                sql += " AND market_cap > 10"
            elif market_cap_filter == "Mid Cap (2B-10B)":
                sql += " AND market_cap BETWEEN 2 AND 10"
            elif market_cap_filter == "Small Cap (<2B)":
                sql += " AND market_cap < 2"
            
        print(f"Executing SQL: {sql} | Params: {params}") # Debug print

        conn = get_db_connection()
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        results = [dict(r) for r in rows]
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print(f"Starting server... DB Path: {db_path}")
    app.run(port=5000, debug=True)
