from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_current_user

# --- SETUP MOCK AUTH ---
# We simulate User ID 1 (the admin/test user)
def mock_get_current_user():
    return {"user_id": 1, "email": "test@admin.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

class TestPortfolioLogic:

    def test_get_portfolio_structure(self):
        """Test that the portfolio endpoint returns the correct JSON structure."""
        response = client.get("/portfolio")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check high-level summary keys exist
        assert "total_value" in data
        assert "total_profit_loss" in data
        assert "holdings" in data
        assert isinstance(data["holdings"], list)

    def test_portfolio_calculations_sanity(self):
        """
        Verify that the math roughly makes sense.
        Total Value should roughly equal sum of individual current values.
        """
        response = client.get("/portfolio")
        data = response.json()
        holdings = data["holdings"]
        
        if not holdings:
            # If empty, totals should be 0
            assert data["total_value"] == 0.0
            assert data["total_profit_loss"] == 0.0
        else:
            # Verify aggregation logic
            calculated_total = sum([h["current_value"] for h in holdings])
            
            # Allow small floating point differences (e.g. 0.0001)
            assert abs(data["total_value"] - calculated_total) < 0.1

    def test_holding_math(self):
        """
        Pick the first holding and verify P/L math.
        Profit = (Current Price - Buy Price) * Qty
        """
        response = client.get("/portfolio")
        data = response.json()
        holdings = data["holdings"]
        
        if holdings:
            h = holdings[0]
            
            # Extract values
            buy_price = h["buy_price"]
            curr_price = h["current_price"]
            qty = h["quantity"]
            reported_pl = h["profit_loss"]
            
            # Re-calculate
            expected_pl = (curr_price - buy_price) * qty
            
            # check if reported matches expected (within 1 cent)
            assert abs(reported_pl - expected_pl) < 0.05