from datetime import datetime
from database import get_connection, get_screening_data
from parser import parse_query_to_dsl


# -------------------------------------
# ALERT EVALUATION
# -------------------------------------
def evaluate_alerts(username: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT alert_id, query
        FROM alerts
        WHERE username = ? AND is_active = 1
    """, (username,))
    alerts = cur.fetchall()

    triggered_results = []

    for alert_id, query in alerts:

        dsl = parse_query_to_dsl(query)
        stocks = get_screening_data(dsl)

        for stock in stocks:

            symbol = stock.get("symbol")

            # Check already triggered
            cur.execute("""
                SELECT 1 FROM alert_triggers
                WHERE alert_id = ? AND symbol = ?
            """, (alert_id, symbol))

            if cur.fetchone():
                continue

            current_price = stock.get("current_price")
            target_price = stock.get("target_price")
            recommendation = stock.get("recommendation")

            upside_percent = None
            if current_price and target_price:
                upside_percent = round(
                    ((target_price - current_price) / current_price) * 100, 2
                )

            # Insert trigger
            cur.execute("""
                INSERT INTO alert_triggers (
                    alert_id,
                    symbol,
                    triggered_at
                )
                VALUES (?, ?, ?)
            """, (
                alert_id,
                symbol,
                datetime.utcnow().isoformat()
            ))

            triggered_results.append({
                "alert_id": alert_id,
                "symbol": symbol,
                "current_price": current_price,
                "target_price": target_price,
                "upside_percent": upside_percent,
                "recommendation": recommendation
            })

    conn.commit()
    conn.close()

    return triggered_results


# -------------------------------------
# ALERT STATUS
# -------------------------------------
def list_alert_status(username: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT alert_id, query, is_active
        FROM alerts
        WHERE username = ?
    """, (username,))
    alerts = cur.fetchall()

    results = []

    for alert_id, query, is_active in alerts:

        cur.execute("""
            SELECT COUNT(*) FROM alert_triggers
            WHERE alert_id = ?
        """, (alert_id,))
        triggered_count = cur.fetchone()[0]

        results.append({
            "alert_id": alert_id,
            "query": query,
            "status": "TRIGGERED" if triggered_count > 0 else "NOT_TRIGGERED",
            "is_active": bool(is_active)
        })

    conn.close()
    return results
