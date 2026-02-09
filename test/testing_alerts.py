"""
Integration tests for alerts: triggers and missing data scenarios.
"""
import sys
import os
import sqlite3
import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "Streamlit_Dashboard"))
sys.path.append(os.path.join(PROJECT_ROOT, "alert_system"))
sys.path.append(os.path.join(PROJECT_ROOT, "tables"))

import server
from alert_engine import AlertEngine
from config import DB_PATH

@pytest.fixture(scope="module")
def client():
    server.app.testing = True
    return server.app.test_client()

def count_events(conn):
    return conn.execute("SELECT COUNT(*) FROM alert_events").fetchone()[0]

class TestAlertsFlow:
    def test_alert_triggers_once(self, client):
        # Arrange
        # Create alert for AAPL above a low threshold to ensure trigger
        res_create = client.post("/alerts", json={"symbol": "AAPL", "condition": "Above price", "value": 1.0})
        assert res_create.status_code == 200
        conn = sqlite3.connect(DB_PATH)
        before = count_events(conn)
        # Act
        res_check1 = client.post("/alerts/checks", json={})
        data1 = res_check1.get_json()
        after1 = count_events(conn)
        res_check2 = client.post("/alerts/checks", json={})
        data2 = res_check2.get_json()
        after2 = count_events(conn)
        conn.close()
        # Assert
        assert res_check1.status_code == 200
        assert res_check2.status_code == 200
        assert after1 >= before
        assert after2 == after1  # no repeat firing
        assert data2["metrics"]["new_events"] == 0

    def test_missing_data_scenario(self):
        # Arrange
        engine = AlertEngine()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Create an empty portfolio 999 with no holdings
        cur.execute("INSERT OR IGNORE INTO portfolios (id, user_id, name) VALUES (999, 1, 'Empty Portfolio')")
        conn.commit()
        cur.execute("INSERT INTO alerts (user_id, portfolio_id, metric, operator, threshold, is_active) VALUES (1, 999, 'price', '>', 1.0, 1)")
        conn.commit()
        before = count_events(conn)
        # Act
        engine.evaluate_alerts()
        after = count_events(conn)
        conn.close()
        # Assert
        assert after == before  # No events recorded due to missing holdings
