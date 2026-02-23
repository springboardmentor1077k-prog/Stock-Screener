from datetime import datetime
from database import get_connection, get_screening_data
from parser import parse_query_to_dsl
from screener import build_where_clause


def evaluate_alerts(username: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, query
        FROM alerts
        WHERE user_id = ?
    """, (username,))
    alerts = cur.fetchall()

    triggered_results = []

    for alert_id, query in alerts:

        try:
            dsl = parse_query_to_dsl(query)
            where_clause = build_where_clause(dsl)
            stocks = get_screening_data(where_clause)
        except Exception:
            continue

        for stock in stocks:

            stock_id = stock.get("stock_id")

            cur.execute("""
                SELECT 1 FROM alert_triggers
                WHERE alert_id = ? AND stock_id = ?
            """, (alert_id, stock_id))

            if cur.fetchone():
                continue

            pe = stock.get("pe_ratio")
            profit = stock.get("profit")

            if pe is not None and profit is not None:
                if pe < 15 and profit > 20000:
                    signal = "BUY"
                    reason = "Low PE with strong profit growth"
                elif pe < 20:
                    signal = "WATCH"
                    reason = "Moderate valuation level"
                else:
                    signal = "RISK"
                    reason = "High PE valuation zone"
            else:
                signal = "WATCH"
                reason = "General market condition"

            cur.execute("""
                INSERT INTO alert_triggers (
                    alert_id,
                    stock_id,
                    triggered_at
                )
                VALUES (?, ?, ?)
            """, (
                alert_id,
                stock_id,
                datetime.utcnow().isoformat()
            ))

            triggered_results.append({
                "alert_id": alert_id,
                "stock_id": stock_id,
                "symbol": stock.get("symbol"),
                "current_price": stock.get("close_price"),
                "signal": signal,
                "reason": reason,
                "triggered_at": datetime.utcnow().isoformat()
            })

    conn.commit()
    conn.close()

    return triggered_results


def list_alert_status(username: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, query
        FROM alerts
        WHERE user_id = ?
    """, (username,))
    alerts = cur.fetchall()

    results = []

    for alert_id, query in alerts:

        cur.execute("""
            SELECT COUNT(*) FROM alert_triggers
            WHERE alert_id = ?
        """, (alert_id,))
        triggered_count = cur.fetchone()[0]

        results.append({
            "alert_id": alert_id,
            "query": query,
            "status": "TRIGGERED" if triggered_count > 0 else "NOT_TRIGGERED"
        })

    conn.close()
    return results
