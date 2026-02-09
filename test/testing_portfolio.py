"""
Integration tests for portfolio calculations and empty states.
"""
import sys
import os
import sqlite3
import pytest
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "Streamlit_Dashboard"))
sys.path.append(os.path.join(PROJECT_ROOT, "tables"))

import server
from config import DB_PATH

@pytest.fixture(scope="module")
def client():
    server.app.testing = True
    return server.app.test_client()

class TestPortfolio:
    def test_profit_loss_accuracy_and_aggregation(self, client):
        # Arrange
        res = client.get("/portfolio")
        data = res.get_json()
        assert res.status_code == 200
        assert data["status"] == "success"
        rows = data["data"]
        if not rows:
            pytest.skip("Portfolio empty; skipping aggregation accuracy test")

        # Act
        df = pd.DataFrame(rows)
        total_value = float((df["current_price"] * df["quantity"]).sum())
        total_pl = float(df["profit_loss"].sum())

        # Assert
        assert "current_price" in df.columns
        assert "profit_loss" in df.columns
        assert total_value >= 0
        # basic sanity: profit_loss equals (price - avg)*qty row-wise sum
        calc_pl = float(((df["current_price"] - df["avg_buy_price"]) * df["quantity"]).sum())
        assert pytest.approx(total_pl, rel=1e-6) == calc_pl

    def test_empty_portfolio_handling(self, client):
        # Arrange: temporarily clear holdings and restore
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM portfolio_holdings WHERE portfolio_id = 1")
        backup = cur.fetchall()
        cur.execute("DELETE FROM portfolio_holdings WHERE portfolio_id = 1")
        conn.commit()
        try:
            # Act
            res = client.get("/portfolio")
            data = res.get_json()
            # Assert
            assert res.status_code == 200
            assert data["status"] == "success"
            assert isinstance(data["data"], list)
            assert len(data["data"]) == 0
        finally:
            # Restore
            for row in backup:
                # row: (id, portfolio_id, stock_id, quantity, avg_buy_price, created_at, updated_at)
                cur.execute(
                    "INSERT INTO portfolio_holdings (portfolio_id, stock_id, quantity, avg_buy_price, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (row[1], row[2], row[3], row[4], row[5], row[6]),
                )
            conn.commit()
            conn.close()
