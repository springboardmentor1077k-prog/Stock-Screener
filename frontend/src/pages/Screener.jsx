import AIScreener from "../components/screener/AIScreener";
import ManualScreener from "../components/screener/ManualScreener";

export default function Screener() {
  return (
    <div className="page">
      <h1>Stock Screener</h1>
      <AIScreener />
      <ManualScreener />
    </div>
  );
}
