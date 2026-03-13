import { useState } from "react";
import API from "../../services/api";
import StockTable from "../ui/StockTable";

export default function ManualScreener() {
  const [pe, setPe] = useState("");
  const [stocks, setStocks] = useState([]);

  const runManual = async () => {
  try {
    const res = await API.get("/stocks/screener", {
      params: { pe },
    });

    setStocks(res.data.data || []);
  } catch (err) {
    console.error(err);
  }
};

  return (
    <div className="module">
      <h2>Manual Screener</h2>
      <input
        type="number"
        placeholder="Max PE Ratio"
        value={pe}
        onChange={(e) => setPe(e.target.value)}
      />
      <button onClick={runManual}>Filter</button>
      <StockTable stocks={stocks} />
    </div>
  );
}
