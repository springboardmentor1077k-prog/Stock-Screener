import { useEffect, useState } from "react";
import API from "../services/api";
import StockTable from "../components/ui/StockTable";

export default function Watchlist() {

  const [stocks, setStocks] = useState([]);

  useEffect(() => {

    const fetchWatchlist = async () => {
      try {

        const res = await API.get("/watchlist");

        console.log("Watchlist data:", res.data); // debug

        setStocks(res.data.data);   // ⭐ important

      } catch (error) {

        console.error("Watchlist error:", error);

      }
    };

    fetchWatchlist();

  }, []);

  if (!stocks || stocks.length === 0) {
    return (
      <div className="page">
        <h1>Watchlist</h1>
        <p>No stocks added to watchlist yet.</p>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Watchlist</h1>
      <StockTable stocks={stocks} />
    </div>
  );
}