export function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export function ErrorBanner({ message }) {
  if (!message) return null;
  return <div className="error-banner">{message}</div>;
}

export function SuccessBanner({ message }) {
  if (!message) return null;
  return <div className="success-banner">{message}</div>;
}

export function RiskBadge({ tier }) {
  const level = (tier || "").replace(" Risk", "");
  const cls = level === "High" ? "high" : level === "Medium" ? "medium" : "low";
  return <span className={`badge ${cls}`}>{level} Risk</span>;
}

export function DatasetPicker({ datasets, value, onChange }) {
  return (
    <div className="form-row">
      <label>Dataset</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">-- Select a dataset --</option>
        {datasets.map((d) => (
          <option key={d.dataset_id} value={d.dataset_id}>
            {d.filename} ({d.rows} rows)
          </option>
        ))}
      </select>
    </div>
  );
}
