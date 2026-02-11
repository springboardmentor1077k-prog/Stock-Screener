from flask import Flask, request, jsonify
import sqlite3
import os
import sys
import json
import time

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
sys.path.append(os.path.join(project_root, "alert_system"))
try:
    from alert_engine import AlertEngine
    alert_engine = AlertEngine(db_path=db_path)
except Exception:
    alert_engine = None

# --- Redis Setup ---
CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))
redis_client = None
def init_redis():
    global redis_client
    if redis_client is not None:
        return redis_client
    try:
        import redis
        redis_client = redis.Redis(host="localhost", port=6379, db=0)
        # Ping to verify
        redis_client.ping()
        print("Redis connected")
    except Exception as e:
        # Fallback to FakeRedis for local demo if real Redis not available
        try:
            import fakeredis
            redis_client = fakeredis.FakeStrictRedis()
            print(f"Using FakeRedis in-memory (Redis unavailable: {e})")
        except Exception as fe:
            redis_client = None
            print(f"Redis unavailable and FakeRedis not usable: {e} | {fe}")
    return redis_client

def make_cache_key(endpoint: str, payload: dict) -> str:
    try:
        s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    except Exception:
        s = str(payload)
    import hashlib
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return f"{endpoint}:{h}"

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
        
        # --- Redis Cache Check ---
        rc = init_redis()
        cache_payload = {
            "query": query,
            "sector": sector,
            "strong_only": strong_only,
            "market_cap": market_cap_filter
        }
        cache_key = make_cache_key("screener", cache_payload)
        start_time = time.time()
        if rc:
            try:
                cached = rc.get(cache_key)
                if cached:
                    print("CACHE HIT:", cache_key)
                    resp = json.loads(cached.decode("utf-8"))
                    resp["cached"] = True
                    resp["latency_ms"] = int((time.time() - start_time) * 1000)
                    return jsonify(resp)
                else:
                    print("CACHE MISS:", cache_key)
            except Exception as e:
                print(f"Cache read error: {e}")

        # Check if it's a "Sentence Query" (Longer, natural language)
        # Simple heuristic: if it contains spaces and > 1 word, treat as NL unless it's just a name
        is_natural_language = len(query.split()) > 2 or any(k in query.lower() for k in ["show", "find", "where", "stocks", "sector", "price", "pe ratio"])

        if is_natural_language:
            # --- AI / Natural Language Processing Path ---
            print(f"Processing Natural Language Query: {query}")
            ai_result = ai_backend.process_query(query)
            
            if not ai_result["is_valid"]:
                print("Compliance rejection")
                return jsonify({"errorCode": "unsupported_query"}), 400
            
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
        response_obj = {"status": "success", "data": results}
        
        # Store in cache with TTL
        if rc:
            try:
                rc.setex(cache_key, CACHE_TTL, json.dumps(response_obj))
            except Exception as e:
                print(f"Cache write error: {e}")
        
        response_obj["cached"] = False
        response_obj["latency_ms"] = int((time.time() - start_time) * 1000)
        return jsonify(response_obj)
    except Exception as e:
        return jsonify({"message": "System error. Please try again later."}), 500

@app.route('/portfolio', methods=['GET'])
def get_portfolio():
    try:
        portfolio_id = 1  # Demo user
        conn = get_db_connection()
        
        # Ensure portfolio exists
        p_check = conn.execute("SELECT id FROM portfolios WHERE id = ?", (portfolio_id,)).fetchone()
        if not p_check:
            conn.execute("INSERT INTO portfolios (id, user_id, name) VALUES (?, ?, ?)", (portfolio_id, 1, "My Portfolio"))
            conn.commit()

        sql = """
        SELECT 
            h.stock_id as symbol,
            h.quantity,
            h.avg_buy_price,
            s.price as current_price,
            s.company_name,
            (s.price - h.avg_buy_price) * h.quantity as profit_loss
        FROM portfolio_holdings h
        JOIN stocks s ON h.stock_id = s.symbol
        WHERE h.portfolio_id = ?
        """
        rows = conn.execute(sql, (portfolio_id,)).fetchall()
        conn.close()
        return jsonify({"status": "success", "data": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"message": "System error. Please try again later."}), 500

@app.route('/alerts', methods=['GET', 'POST'])
def handle_alerts():
    conn = get_db_connection()
    portfolio_id = 1
    
    if request.method == 'GET':
        try:
            # We are storing "SYMBOL price" in metric for now to link to stock
            rows = conn.execute("SELECT * FROM alerts WHERE portfolio_id = ?", (portfolio_id,)).fetchall()
            conn.close()
            return jsonify({"status": "success", "data": [dict(r) for r in rows]})
        except Exception as e:
            conn.close()
            return jsonify({"message": "System error. Please try again later."}), 500

    elif request.method == 'POST':
        try:
            data = request.get_json()
            symbol = data.get('symbol')
            condition = data.get('condition') # "Above price" or "Below price"
            value = float(data.get('value'))
            
            # Map condition to operator
            operator = ">" if "Above" in condition else "<"
            metric = f"{symbol} price"
            
            conn.execute(
                "INSERT INTO alerts (user_id, portfolio_id, metric, operator, threshold) VALUES (?, ?, ?, ?, ?)",
                (1, portfolio_id, metric, operator, value)
            )
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "Alert created"})
        except Exception as e:
            conn.close()
            return jsonify({"message": "System error. Please try again later."}), 500

@app.route('/alerts/checks', methods=['POST'])
def check_alerts():
    try:
        conn = get_db_connection()
        before_total = conn.execute(
            "SELECT COUNT(*) FROM alert_events"
        ).fetchone()[0]
        if alert_engine:
            alert_engine.evaluate_alerts()
        after_total = conn.execute(
            "SELECT COUNT(*) FROM alert_events"
        ).fetchone()[0]
        delta = after_total - before_total
        portfolio_id = 1
        events_sql = """
        SELECT e.id, e.alert_id, e.stock_id, e.triggered_value, e.triggered_at
        FROM alert_events e
        JOIN alerts a ON a.id = e.alert_id
        WHERE a.portfolio_id = ?
        ORDER BY e.triggered_at DESC
        LIMIT 50
        """
        rows = conn.execute(events_sql, (portfolio_id,)).fetchall()
        conn.close()
        message = "No new alerts fired" if delta == 0 else f"{delta} alert(s) fired"
        return jsonify({
            "status": "success",
            "message": message,
            "metrics": {
                "total_events": after_total,
                "new_events": delta
            },
            "data": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"message": "System error. Please try again later."}), 500

if __name__ == '__main__':
    print(f"Starting server... DB Path: {db_path}")
    app.run(port=5000, debug=True)
