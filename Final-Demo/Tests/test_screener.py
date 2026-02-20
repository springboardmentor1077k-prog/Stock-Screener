from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_current_user

# --- SETUP MOCK AUTH ---
# We force the app to believe a user is already logged in.
def mock_get_current_user():
    return {"user_id": 1, "email": "test@admin.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

class TestScreenerAPI:

    def test_screener_successful_query(self):
        """Test a broad query that should return results."""
        # Note: If you renamed your endpoint to /screen, update the URL below!
        response = client.post("/nl-query", json={"query": "PE < 50"})
        
        # 1. Check API Status
        assert response.status_code == 200
        
        # 2. Check Response Structure
        data = response.json()
        assert "results" in data
        assert "dsl" in data
        assert isinstance(data["results"], list)
        
        # 3. If your DB has data (from setup_portfolio), we might expect results
        # (Optional: depends if your local DB is empty or not)
        # assert len(data["results"]) > 0 

    def test_screener_no_results(self):
        """Test a query that is mathematically impossible."""
        response = client.post("/nl-query", json={"query": "PE < 0"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return valid JSON but empty list
        assert data["results"] == []

    def test_screener_invalid_dsl_handling(self):
        """Test how the API handles a nonsensical query."""
        # "Show me the moon" -> might default to Technology or return empty, 
        # but it MUST NOT crash (500 error).
        response = client.post("/nl-query", json={"query": "Show me the moon"})
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["results"], list)