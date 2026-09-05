import { useEffect, useState } from "react";
import { predictionHistory } from "../api/client";
import { RiskBadge } from "../components/Common";

export default function HistoryPage() {
  const [items, setItems] = useState([]);

  useEffect(() => { predictionHistory(100).then((r) => setItems(r.data.predictions)); }, []);

  return (
    <div>
      <div className="page-title">Prediction History</div>
      <div className="page-subtitle">Log of all individual and batch predictions made with this system.</div>

      <div className="card">
        {items.length === 0 && <div className="empty-state">No predictions made yet.</div>}
        {items.length > 0 && (
          <table>
            <thead>
              <tr><th>Type</th><th>Date</th><th>Model ID</th><th>Result / Summary</th></tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.prediction_id}>
                  <td>{p.type}</td>
                  <td>{new Date(p.predicted_at).toLocaleString()}</td>
                  <td style={{ fontSize: 11 }}>{p.model_id?.slice(0, 8)}…</td>
                  <td>
                    {p.type === "individual" ? (
                      <>
                        {(p.result.churn_probability * 100).toFixed(1)}% &nbsp;
                        <RiskBadge tier={p.result.risk_level} />
                      </>
                    ) : (
                      <>
                        {p.summary.total_customers} customers · {p.summary.predicted_churn} predicted churn ·{" "}
                        <span className="badge high">{p.summary.high_risk} high risk</span>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
