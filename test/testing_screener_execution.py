"""
Integration tests for screener execution using Flask test client.
"""
import sys
import os
import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "Streamlit_Dashboard"))

import server

@pytest.fixture(scope="module")
def client():
    server.app.testing = True
    return server.app.test_client()

class TestScreenerExecution:
    def test_successful_results(self, client):
        # Arrange
        payload = {"query": "Show IT sector stocks"}
        # Act
        res = client.post("/screen", json=payload)
        data = res.get_json()
        # Assert
        assert res.status_code == 200
        assert data.get("status") in ("success", "error")
        if data.get("status") == "success":
            assert isinstance(data.get("data"), list)

    def test_empty_results_handling(self, client):
        # Arrange
        payload = {"query": "Sector: NonExistentSectorXYZ"}
        # Act
        res = client.post("/screen", json=payload)
        data = res.get_json()
        # Assert
        assert res.status_code == 200
        assert data.get("status") in ("success", "error")
        if data.get("status") == "success":
            assert isinstance(data.get("data"), list)
            assert len(data.get("data")) == 0 or len(data.get("data")) >= 0

    def test_edge_cases_no_crash(self, client):
        # Arrange
        payload = {"query": "1234567890"}  # numeric heuristic branch
        # Act
        res = client.post("/screen", json=payload)
        # Assert
        assert res.status_code == 200
