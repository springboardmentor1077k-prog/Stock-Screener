import { useEffect, useState } from "react";
import API from "../services/api";

export default function Dashboard() {
  const [stats, setStats] = useState({
    stocks: 0,
    alerts: 0,
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const stocksRes = await API.get("/stocks");
        const alertsRes = await API.get("/alerts");

        setStats({
          stocks: stocksRes.data.count || 0,
          alerts: alertsRes.data.alerts?.length || 0,
        });

      } catch (err) {
        console.error("Dashboard fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) return <p>Loading dashboard...</p>;

  return (
    <div className="dashboard">
      <h2>Dashboard Overview</h2>

      <div className="dashboard-cards">
        <div className="card">
          <h3>Total Stocks</h3>
          <p>{stats.stocks}</p>
        </div>

        <div className="card">
          <h3>Active Alerts</h3>
          <p>{stats.alerts}</p>
        </div>
      </div>
    </div>
  );
}