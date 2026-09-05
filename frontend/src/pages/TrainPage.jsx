import { useEffect, useState } from "react";
import { listDatasets, trainModels } from "../api/client";
import { DatasetPicker, ErrorBanner, SuccessBanner } from "../components/Common";
import { useAppCtx } from "../AppContext";
import { useNavigate } from "react-router-dom";

export default function TrainPage() {
  const { datasetId, selectDataset, selectModel } = useAppCtx();
  const [datasets, setDatasets] = useState([]);
  const [testSize, setTestSize] = useState(0.2);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [result, setResult] = useState(null);
  const navigate = useNavigate();

  useEffect(() => { listDatasets().then((r) => setDatasets(r.data.datasets)); }, []);

  const handleTrain = async () => {
    setLoading(true);
    setError("");
    setSuccess("");
    setResult(null);
    try {
      const res = await trainModels({ dataset_id: datasetId, test_size: parseFloat(testSize) });
      setResult(res.data.model);
      selectModel(res.data.model.model_id);
      setSuccess(`Training complete. Best model: ${res.data.model.best_model_name.toUpperCase()}`);
    } catch (e) {
      setError(e.response?.data?.detail || "Training failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-title">Model Training</div>
      <div className="page-subtitle">
        Runs the full ML pipeline: feature engineering → train/test split → train XGBoost, Logistic
        Regression & Random Forest → evaluate → select best model.
      </div>

      <div className="card">
        <ErrorBanner message={error} />
        <SuccessBanner message={success} />
        <DatasetPicker datasets={datasets} value={datasetId} onChange={selectDataset} />
        <div className="form-row" style={{ maxWidth: 200 }}>
          <label>Test set size</label>
          <select value={testSize} onChange={(e) => setTestSize(e.target.value)}>
            <option value="0.1">10%</option>
            <option value="0.2">20%</option>
            <option value="0.3">30%</option>
          </select>
        </div>
        <button className="btn" onClick={handleTrain} disabled={!datasetId || loading}>
          {loading ? "Training models..." : "Train & Compare Models"}
        </button>
      </div>

      {result && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>
            Best Model: <span className="badge best">{result.best_model_name.toUpperCase()}</span>
          </h3>
          <p style={{ color: "#93a0bd" }}>
            Model ID: {result.model_id} · Trained on {result.train_rows} rows, tested on {result.test_rows} rows.
          </p>
          <button className="btn secondary" onClick={() => navigate("/models")}>
            View Full Comparison & SHAP →
          </button>
        </div>
      )}
    </div>
  );
}
