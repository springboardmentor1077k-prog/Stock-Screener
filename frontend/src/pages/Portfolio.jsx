import { useEffect, useState } from "react";
import API from "../services/api";
import Loader from "../components/ui/Loader";
import ErrorBanner from "../components/ui/ErrorBanner";

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    symbol: "",
    quantity: "",
    buy_price: ""
  });

  // ==============================
  // Fetch Portfolio
  // ==============================
  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      setError("");

      const res = await API.get("/portfolio");

      setPortfolio(res.data.holdings || []);
      setSummary(res.data.summary || null);
    } catch (err) {
      console.error(err);
      setError("Failed to load portfolio.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  // ==============================
  // Add Stock
  // ==============================
  const addStock = async () => {
    try {
      if (!form.symbol || !form.quantity || !form.buy_price) {
        alert("Please fill all fields");
        return;
      }

      await API.post("/portfolio", {
        symbol: form.symbol.toUpperCase(),
        quantity: Number(form.quantity),
        buy_price: Number(form.buy_price)
      });

      setForm({ symbol: "", quantity: "", buy_price: "" });
      fetchPortfolio();
    } catch (err) {
      console.error(err);
      setError("Failed to add stock.");
    }
  };

  // ==============================
  // Delete Stock
  // ==============================
  const deleteStock = async (id) => {
    try {
      await API.delete(`/portfolio/${id}`);
      fetchPortfolio();
    } catch (err) {
      console.error(err);
      setError("Failed to delete stock.");
    }
  };

  return (
    <div className="page">
      <h1>Portfolio</h1>

      {loading && <Loader />}
      {error && <ErrorBanner message={error} />}

      {/* ================= Add Form ================= */}
      <div className="module">
        <h3>Add Holding</h3>

        <input
          placeholder="Symbol (AAPL)"
          value={form.symbol}
          onChange={(e) =>
            setForm({ ...form, symbol: e.target.value })
          }
        />

        <input
          type="number"
          placeholder="Quantity"
          value={form.quantity}
          onChange={(e) =>
            setForm({ ...form, quantity: e.target.value })
          }
        />

        <input
          type="number"
          placeholder="Buy Price"
          value={form.buy_price}
          onChange={(e) =>
            setForm({ ...form, buy_price: e.target.value })
          }
        />

        <button onClick={addStock}>Add</button>
      </div>

      {/* ================= Summary ================= */}
      {summary && (
        <div className="card">
          <h3>Summary</h3>
          <p>
            Total Invested: $
            {Number(summary.totalInvested || 0).toFixed(2)}
          </p>
          <p>
            Total Current: $
            {Number(summary.totalCurrent || 0).toFixed(2)}
          </p>
          <p>
            P/L: $
            {Number(summary.totalProfitLoss || 0).toFixed(2)}
          </p>
        </div>
      )}

      {/* ================= Table ================= */}
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Qty</th>
            <th>Buy</th>
            <th>Current</th>
            <th>P/L</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {portfolio.length === 0 ? (
            <tr>
              <td colSpan="6">No holdings found</td>
            </tr>
          ) : (
            portfolio.map((p) => (
              <tr key={p.id}>
                <td>{p.symbol}</td>
                <td>{p.quantity}</td>
                <td>{p.buy_price}</td>
                <td>{p.current_price}</td>
                <td>{p.profit_loss}</td>
                <td>
                  <button onClick={() => deleteStock(p.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
