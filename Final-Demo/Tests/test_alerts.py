from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_current_user, get_db

# --- SETUP MOCK AUTH ---
# We simulate User ID 1 (the admin/test user)
def mock_get_current_user():
    return {"user_id": 1, "email": "test@admin.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

class TestAlertsLogic:

    def test_1_create_alert(self):
        """Test creating a new monitoring rule."""
        payload = {
            "metric": "price",
            "operator": ">",
            "threshold": 0.01 # This is guaranteed to trigger for any valid stock
        }
        response = client.post("/alerts", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "alert_id" in data
        assert data["message"] == "Alert created"
        
        # Save ID for later if needed (though next tests just run 'check all')
        return data["alert_id"]

    def test_2_trigger_alert_first_time(self):
        """Test that running the check triggers our new rule."""
        # This endpoint runs evaluate_alerts_logic()
        response = client.post("/alerts/check")
        
        assert response.status_code == 200
        data = response.json()
        
        # Expectation: Since Price > 0.01 is true for everything, 
        # we should see at least 1 new trigger.
        assert data["status"] == "success"
        assert data["new_events_triggered"] > 0 

    def test_3_trigger_alert_idempotency(self):
        """Test that running the check AGAIN does NOT re-trigger."""
        # The 'Trigger Once' logic means this second run should return 0 new events
        response = client.post("/alerts/check")
        
        assert response.status_code == 200
        data = response.json()
        
        # Expectation: 0 new triggers because they are already recorded in alert_events
        assert data["new_events_triggered"] == 0

    def test_4_get_alert_history(self):
        """Test fetching the history to see the event we just created."""
        response = client.get("/alerts")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check we have active rules
        assert len(data["alerts"]) > 0
        
        # Check we have trigger events
        assert len(data["events"]) > 0
        
        # Verify structure of event
        event = data["events"][0]
        assert "ticker" in event
        assert "triggered_value" in event