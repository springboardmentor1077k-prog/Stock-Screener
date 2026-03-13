import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import API from "../services/api";
import Loader from "../components/ui/Loader";
import ErrorBanner from "../components/ui/ErrorBanner";

export default function Alerts() {
  const location = useLocation();
  const prefillSymbol = location.state?.symbol || "";

  const [alerts, setAlerts] = useState([]);
  const [alertName, setAlertName] = useState("");
  const [symbol, setSymbol] = useState(prefillSymbol);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // ================= FETCH ALERTS =================
  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const res = await API.get("/alerts");
      setAlerts(res.data.alerts || []);
    } catch {
      setError("Failed to load alerts");
    } finally {
      setLoading(false);
    }
  };

  // ================= CREATE ALERT =================
  const createAlert = async () => {
    if (!alertName.trim() || !symbol.trim()) {
      setError("Alert name and symbol are required");
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      await API.post("/alerts", {
        name: alertName,
        dsl: {
          conditions: [
            {
              field: "symbol",
              operator: "=",
              value: symbol.toUpperCase(),
            },
          ],
        },
      });

      setSuccess("Alert created successfully");
      setAlertName("");
      setSymbol("");
      fetchAlerts();
    } catch (err) {
      setError(err.response?.data?.message || "Failed to create alert");
    } finally {
      setSubmitting(false);
    }
  };

  // ================= DELETE ALERT =================
  const deleteAlert = async (id) => {
    try {
      await API.delete(`/alerts/${id}`);
      setAlerts(alerts.filter((a) => a.id !== id));
      setSuccess("Alert deleted");
    } catch {
      setError("Failed to delete alert");
    }
  };

  // ================= LIFECYCLE =================
  useEffect(() => {
    fetchAlerts();
  }, []);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(""), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  // ================= UI =================
  return (
    <div className="alerts-page">
      <h2>Stock Alerts</h2>

      <div className="create-alert-card">
        <h3>Create New Alert</h3>

        <input
          placeholder="Alert Name (e.g. INFY Price Alert)"
          value={alertName}
          onChange={(e) => setAlertName(e.target.value)}
        />

        <input
          placeholder="Stock Symbol (e.g. INFY)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />

        <button onClick={createAlert} disabled={submitting}>
          {submitting ? "Creating..." : "Create Alert"}
        </button>
      </div>

      {loading && <Loader />}
      {error && <ErrorBanner message={error} />}
      {success && <div className="success-banner">{success}</div>}

      <div className="alerts-list">
        <h3>Active Alerts</h3>

        {!loading && alerts.length === 0 && (
          <div className="empty-state">
            <p>No alerts created yet.</p>
            <span>Create your first smart alert above.</span>
          </div>
        )}

        {alerts.map((a) => (
          <div key={a.id} className="alert-card">
            <div>
              <strong>{a.name}</strong>
              <p className="trigger-time">
                Last Triggered:{" "}
                {a.last_triggered_at
                  ? new Date(a.last_triggered_at).toLocaleString()
                  : "Never"}
              </p>
            </div>

            <button
              className="delete-btn"
              onClick={() => deleteAlert(a.id)}
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}