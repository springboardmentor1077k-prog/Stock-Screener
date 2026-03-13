import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import API from "../services/api";
import Loader from "../components/ui/Loader";
import ErrorBanner from "../components/ui/ErrorBanner";

export default function Advisory() {
  const { symbol } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAdvisory = async () => {
      try {
        setLoading(true);
        const res = await API.get(`/advisory/${symbol}`);
        setData(res.data.data);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to fetch advisory");
      } finally {
        setLoading(false);
      }
    };

    fetchAdvisory();
  }, [symbol]);

  if (loading) return <Loader />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  const { quantitativeScore, riskLevel, aiAdvisory } = data;

  const getRecommendationColor = (rec) => {
    if (rec === "BUY") return "green";
    if (rec === "SELL") return "red";
    return "orange";
  };

  return (
    <div className="advisory-page">
      <h2>{data.symbol} Advisory Report</h2>

      <div className="advisory-top">
        <div className="score-card">
          <h3>Quantitative Score</h3>
          <div className="score-value">{quantitativeScore} / 10</div>
        </div>

        <div className="risk-card">
          <h3>Risk Level</h3>
          <span className={`risk-badge ${riskLevel.toLowerCase()}`}>
            {riskLevel}
          </span>
        </div>

        <div className="recommendation-card">
          <h3>Recommendation</h3>
          <span
            className="recommendation-badge"
            style={{
              background: getRecommendationColor(aiAdvisory.recommendation),
            }}
          >
            {aiAdvisory.recommendation}
          </span>
        </div>
      </div>

      <div className="confidence-section">
        <h3>Confidence Level</h3>
        <div className="confidence-bar">
          <div
            className="confidence-fill"
            style={{ width: `${aiAdvisory.confidence}%` }}
          ></div>
        </div>
        <p>{aiAdvisory.confidence}%</p>
      </div>

      <div className="summary-section">
        <h3>Summary</h3>
        <p>{aiAdvisory.summary}</p>
      </div>

      <div className="analysis-section">
        <div className="strengths">
          <h3>Strengths</h3>
          <ul>
            {aiAdvisory.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>

        <div className="risks">
          <h3>Risks</h3>
          <ul>
            {aiAdvisory.risks.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}