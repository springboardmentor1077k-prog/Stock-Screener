import { useState } from "react";
import API from "../../services/api";
import StockTable from "../ui/StockTable";
import Loader from "../ui/Loader";
import ErrorBanner from "../ui/ErrorBanner";

export default function AIScreener() {
  const [query, setQuery] = useState("");
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runAI = async () => {
  try {
    setLoading(true);
    setError("");

    const res = await API.post("/stocks/ai-screener", {
      query,
    });

    setStocks(res.data.data || []);
  } catch (err) {
    setError(err.response?.data?.message || "AI Screener failed");
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="module">
      <h2>AI Screener</h2>
      <textarea
        placeholder="Show top 5 stocks with PE less than 30"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={runAI}>Run AI</button>
      {loading && <Loader />}
      <ErrorBanner message={error} />
      <StockTable stocks={stocks} />
    </div>
  );
}
