import { useEffect, useState } from "react";
import { listModels, predict } from "../api/client";
import { ErrorBanner, RiskBadge } from "../components/Common";
import { useAppCtx } from "../AppContext";

// Common churn dataset fields (Telco-style); extra/missing fields are handled gracefully server-side.
const FIELDS = [
  "gender", "SeniorCitizen", "Partner", "Dependents", "tenure",
  "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
  "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
  "Contract", "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges",
];

export default function PredictIndividualPage() {
  const { modelId, selectModel } = useAppCtx();
  const [models, setModels] = useState([]);
  const [formValues, setFormValues] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listModels().then((r) => {
      setModels(r.data.models);
      if (!modelId && r.data.models[0]) selectModel(r.data.models[0].model_id);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = (field, value) => setFormValues((prev) => ({ ...prev, [field]: value }));

  const handlePredict = async () => {
    setError("");
    setResult(null);
    if (!modelId) { setError("Select a trained model first."); return; }
    setLoading(true);
    try {
      const res = await predict({ model_id: modelId, customer_data: formValues });
      setResult(res.data);
    } catch (e) {
      const detail = e.response?.data?.detail;
      if (!e.response || (e.response.status >= 500 && !detail)) {
        setError("Cannot reach the prediction service. Is the backend running?");
      } else {
        setError(
          Array.isArray(detail)
            ? detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join("; ")
            : detail || "Prediction failed."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-title">Individual Churn Prediction</div>
      <div className="page-subtitle">Enter a single customer's attributes to get a churn probability and risk classification.</div>

      <div className="card">
        <ErrorBanner message={error} />
        <div className="form-row" style={{ maxWidth: 400 }}>
          <label>Trained model</label>
          <select value={modelId} onChange={(e) => selectModel(e.target.value)}>
            <option value="">-- Select model --</option>
            {models.map((m) => (
              <option key={m.model_id} value={m.model_id}>
                {new Date(m.trained_at).toLocaleString()} — {m.best_model_name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-3">
          {FIELDS.map((f) => (
            <div className="form-row" key={f}>
              <label>{f}</label>
              <input
                type="text"
                placeholder={f}
                value={formValues[f] || ""}
                onChange={(e) => handleChange(f, e.target.value)}
              />
            </div>
          ))}
        </div>
        <button className="btn" onClick={handlePredict} disabled={loading}>
          {loading ? "Predicting..." : "Predict Churn"}
        </button>
      </div>

      {result && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Prediction Result</h3>
          <div className="grid grid-3">
            <div className="stat-card">
              <div className="stat-value">{result.prediction}</div>
              <div className="stat-label">Predicted Outcome</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{(result.churn_probability * 100).toFixed(1)}%</div>
              <div className="stat-label">Churn Probability</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{(result.retention_probability * 100).toFixed(1)}%</div>
              <div className="stat-label">Retention Probability</div>
            </div>
            <div className="stat-card">
              <RiskBadge tier={result.risk_level} />
              <div className="stat-label">Risk Level</div>
            </div>
          </div>
          <div className="form-row" style={{ marginTop: 16 }}>
            <label>Recommendation</label>
            <div>{result.recommendation}</div>
          </div>
          <div className="page-subtitle" style={{ marginTop: 12 }}>
            Model: {result.model_name} &middot; ID: {result.model_id?.slice(0, 8)}…
            {result.model_trained_at && <> &middot; Trained {new Date(result.model_trained_at).toLocaleString()}</>}
          </div>
        </div>
      )}
    </div>
  );
}
