import { useEffect, useState } from "react";
import { listModels } from "../api/client";
import { StatCard } from "../components/Common";
import { useAppCtx } from "../AppContext";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from "recharts";

const MODEL_LABELS = { xgboost: "XGBoost", logistic_regression: "Logistic Regression", random_forest: "Random Forest" };
const METRIC_KEYS = ["accuracy", "precision", "recall", "f1_score", "roc_auc"];

export default function ModelsPage() {
  const { modelId, selectModel } = useAppCtx();
  const [models, setModels] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    listModels().then((r) => {
      setModels(r.data.models);
      const found = r.data.models.find((m) => m.model_id === modelId) || r.data.models[0];
      setSelected(found || null);
      if (found) selectModel(found.model_id);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (models.length === 0) {
    return (
      <div>
        <div className="page-title">Model Comparison & Explainability</div>
        <div className="empty-state">No trained models yet. Go to "Model Training" first.</div>
      </div>
    );
  }

  const comparisonData = selected
    ? Object.entries(selected.all_results).map(([name, m]) => ({ model: MODEL_LABELS[name] || name, ...m }))
    : [];

  const xgb = selected?.all_results?.xgboost;
  const rocData = xgb?.roc_curve || [];
  const bestModel = selected?.best_model_name;
  const featureImportance = selected?.feature_importance?.slice(0, 12) || [];
  const shap = selected?.shap_summary;

  return (
    <div>
      <div className="page-title">Model Comparison & Explainability</div>
      <div className="page-subtitle">Compare XGBoost, Logistic Regression & Random Forest; inspect XGBoost metrics, feature importance and SHAP values.</div>

      <div className="card">
        <div className="form-row" style={{ maxWidth: 400 }}>
          <label>Trained model run</label>
          <select
            value={selected?.model_id || ""}
            onChange={(e) => {
              const m = models.find((mm) => mm.model_id === e.target.value);
              setSelected(m);
              selectModel(m.model_id);
            }}
          >
            {models.map((m) => (
              <option key={m.model_id} value={m.model_id}>
                {new Date(m.trained_at).toLocaleString()} — best: {m.best_model_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 5. Model comparison */}
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Model Comparison (XGBoost vs Logistic Regression vs Random Forest)</h3>
        <table>
          <thead>
            <tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th></th></tr>
          </thead>
          <tbody>
            {comparisonData.map((row) => (
              <tr key={row.model}>
                <td>{row.model}</td>
                <td>{row.accuracy}</td>
                <td>{row.precision}</td>
                <td>{row.recall}</td>
                <td>{row.f1_score}</td>
                <td>{row.roc_auc}</td>
                <td>{row.model === (MODEL_LABELS[bestModel] || bestModel) && <span className="badge best">BEST</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a3552" />
            <XAxis dataKey="model" stroke="#93a0bd" fontSize={12} />
            <YAxis stroke="#93a0bd" fontSize={12} domain={[0, 1]} />
            <Tooltip contentStyle={{ background: "#161d2e", border: "1px solid #2a3552" }} />
            <Legend />
            <Bar dataKey="accuracy" fill="#5b8cff" />
            <Bar dataKey="roc_auc" fill="#38d9a9" />
            <Bar dataKey="f1_score" fill="#ffb84d" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 6. XGBoost performance metrics */}
      {xgb && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>XGBoost Performance Metrics</h3>
          <div className="grid grid-4">
            <StatCard label="Accuracy" value={xgb.accuracy} />
            <StatCard label="Precision" value={xgb.precision} />
            <StatCard label="Recall" value={xgb.recall} />
            <StatCard label="ROC-AUC" value={xgb.roc_auc} />
          </div>

          <h4>Confusion Matrix</h4>
          <table style={{ maxWidth: 320 }}>
            <thead><tr><th></th><th>Pred: No Churn</th><th>Pred: Churn</th></tr></thead>
            <tbody>
              <tr><td>Actual: No Churn</td><td>{xgb.confusion_matrix[0][0]}</td><td>{xgb.confusion_matrix[0][1]}</td></tr>
              <tr><td>Actual: Churn</td><td>{xgb.confusion_matrix[1][0]}</td><td>{xgb.confusion_matrix[1][1]}</td></tr>
            </tbody>
          </table>

          <h4>ROC Curve</h4>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={rocData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3552" />
              <XAxis dataKey="fpr" type="number" domain={[0, 1]} stroke="#93a0bd" fontSize={12} label={{ value: "FPR", position: "insideBottom", fill: "#93a0bd" }} />
              <YAxis dataKey="tpr" type="number" domain={[0, 1]} stroke="#93a0bd" fontSize={12} />
              <Tooltip contentStyle={{ background: "#161d2e", border: "1px solid #2a3552" }} />
              <Line type="monotone" dataKey="tpr" stroke="#5b8cff" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 7. Feature importance / SHAP */}
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Feature Importance ({MODEL_LABELS[bestModel] || bestModel})</h3>
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={featureImportance} layout="vertical" margin={{ left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a3552" />
            <XAxis type="number" stroke="#93a0bd" fontSize={12} />
            <YAxis dataKey="feature" type="category" stroke="#93a0bd" fontSize={12} width={140} />
            <Tooltip contentStyle={{ background: "#161d2e", border: "1px solid #2a3552" }} />
            <Bar dataKey="importance_pct" fill="#38d9a9" radius={[0, 6, 6, 0]} />
          </BarChart>
        </ResponsiveContainer>

        <h4>SHAP Summary (mean |SHAP value| per feature)</h4>
        {shap?.available ? (
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={shap.summary.slice(0, 12)} layout="vertical" margin={{ left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3552" />
              <XAxis type="number" stroke="#93a0bd" fontSize={12} />
              <YAxis dataKey="feature" type="category" stroke="#93a0bd" fontSize={12} width={140} />
              <Tooltip contentStyle={{ background: "#161d2e", border: "1px solid #2a3552" }} />
              <Bar dataKey="mean_abs_shap" fill="#a78bfa" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state">SHAP values unavailable for this run: {shap?.error}</div>
        )}
      </div>
    </div>
  );
}
