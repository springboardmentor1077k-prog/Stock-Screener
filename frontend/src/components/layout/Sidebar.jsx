import { Link } from "react-router-dom";

export default function Sidebar() {
  return (
    <div className="sidebar">
      <h2>StockVision</h2>
      <Link to="/">Dashboard</Link>
      <Link to="/screener">AI Screener</Link>
      <Link to="/stocks">All Stocks</Link>
      <Link to="/watchlist">Watchlist</Link>
      <Link to="/portfolio">Portfolio</Link>

    </div>
  );
}
