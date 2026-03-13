import { useEffect, useState } from "react";
import API from "../services/api";
import StockTable from "../components/ui/StockTable";

export default function AllStocks() {
  const [stocks, setStocks] = useState([]);

  useEffect(() => {
    API.get("/stocks")
      .then(res => setStocks(res.data.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="page">
      <h1>All Stocks</h1>
      <StockTable stocks={stocks} />
    </div>
  );
}
