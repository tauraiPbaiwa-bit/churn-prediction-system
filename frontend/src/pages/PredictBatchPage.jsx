import { useEffect, useState } from "react";
import { listModels, listDatasets, predictBatch } from "../api/client";
import { DatasetPicker, ErrorBanner, StatCard, RiskBadge } from "../components/Common";
import { useAppCtx } from "../AppContext";

export default function PredictBatchPage() {
  const { modelId, selectModel, datasetId, selectDataset } = useAppCtx();
  const [models, setModels] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listModels().then((r) => setModels(r.data.models));
    listDatasets().then((r) => setDatasets(r.data.datasets));
  }, []);

  const handlePredict = async () => {
    setError("");
    setResult(null);
    if (!modelId || !datasetId) { setError("Select both a dataset and a trained model."); return; }
    setLoading(true);
    try {
      const res = await predictBatch({ model_id: modelId, dataset_id: datasetId });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Batch prediction failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-title">Batch Prediction</div>
      <div className="page-subtitle">Run churn prediction across an entire uploaded dataset at once.</div>

      <div className="card">
        <ErrorBanner message={error} />
        <DatasetPicker datasets={datasets} value={datasetId} onChange={selectDataset} />
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
        <button className="btn" onClick={handlePredict} disabled={loading}>
          {loading ? "Running batch prediction..." : "Run Batch Prediction"}
        </button>
      </div>

      {result && (
        <>
          <div className="grid grid-4">
            <StatCard label="Total Customers" value={result.summary.total_customers} />
            <StatCard label="Predicted Churn" value={result.summary.predicted_churn} />
            <StatCard label="High Risk" value={result.summary.high_risk} />
            <StatCard label="Low Risk" value={result.summary.low_risk} />
          </div>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Sample Results (first 50 rows)</h3>
            <div style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    {Object.keys(result.sample_results[0] || {})
                      .filter((k) => !["churn_prediction", "churn_probability", "risk_tier"].includes(k))
                      .map((k) => <th key={k}>{k}</th>)}
                    <th>Probability</th><th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {result.sample_results.map((row, i) => (
                    <tr key={i}>
                      {Object.keys(row)
                        .filter((k) => !["churn_prediction", "churn_probability", "risk_tier"].includes(k))
                        .map((k) => <td key={k}>{String(row[k])}</td>)}
                      <td>{(row.churn_probability * 100).toFixed(1)}%</td>
                      <td><RiskBadge tier={row.risk_tier} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
