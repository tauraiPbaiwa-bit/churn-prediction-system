import { useEffect, useState } from "react";
import { listDatasets, getOverview, runOlapQuery } from "../api/client";
import { StatCard, DatasetPicker, ErrorBanner } from "../components/Common";
import { useAppCtx } from "../AppContext";

const DIMENSIONS = ["Contract", "PaymentMethod", "InternetService", "gender", "tenure"];

export default function OverviewPage() {
  const { datasetId, selectDataset } = useAppCtx();
  const [datasets, setDatasets] = useState([]);
  const [overview, setOverview] = useState(null);
  const [dims, setDims] = useState([]);
  const [measure, setMeasure] = useState("churn_rate");
  const [queryResult, setQueryResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { listDatasets().then((r) => setDatasets(r.data.datasets)); }, []);

  useEffect(() => {
    if (!datasetId) { setOverview(null); return; }
    getOverview(datasetId).then((r) => setOverview(r.data)).catch(() => setOverview(null));
  }, [datasetId]);

  const toggleDim = (d) => {
    setDims((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]));
  };

  const runQuery = async () => {
    setError("");
    if (!datasetId || dims.length === 0) { setError("Select a dataset and at least one dimension."); return; }
    try {
      const res = await runOlapQuery({ dataset_id: datasetId, dimensions: dims, measure });
      setQueryResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Query failed.");
    }
  };

  return (
    <div>
      <div className="page-title">OLAP / Dataset Summary</div>
      <div className="page-subtitle">Multidimensional analysis across contract, tenure, payment method, service type and churn status.</div>

      <div className="card">
        <DatasetPicker datasets={datasets} value={datasetId} onChange={selectDataset} />
      </div>

      {overview && (
        <div className="grid grid-4">
          <StatCard label="Total Customers" value={overview.total_customers} />
          <StatCard label="Total Features" value={overview.total_features} />
          <StatCard label="Overall Churn Rate" value={`${overview.overall_churn_rate ?? "—"}%`} />
          <StatCard label="Churned / Retained" value={`${overview.churned_customers ?? "—"} / ${overview.retained_customers ?? "—"}`} />
        </div>
      )}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Custom OLAP Query (Slice & Dice)</h3>
        <ErrorBanner message={error} />
        <div className="tag-select">
          {DIMENSIONS.map((d) => (
            <div key={d} className={"tag" + (dims.includes(d) ? " active" : "")} onClick={() => toggleDim(d)}>
              {d}
            </div>
          ))}
        </div>
        <div className="form-row" style={{ maxWidth: 260 }}>
          <label>Measure</label>
          <select value={measure} onChange={(e) => setMeasure(e.target.value)}>
            <option value="churn_rate">Churn Rate (%)</option>
            <option value="count">Customer Count</option>
            <option value="avg_tenure">Average Tenure</option>
            <option value="avg_monthly_charges">Average Monthly Charges</option>
          </select>
        </div>
        <button className="btn" onClick={runQuery}>Run Query</button>

        {queryResult && (
          <div style={{ marginTop: 16, overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  {queryResult.dimensions.map((d) => <th key={d}>{d}</th>)}
                  <th>{queryResult.measure}</th>
                  <th>Count</th>
                </tr>
              </thead>
              <tbody>
                {queryResult.result.map((row, i) => (
                  <tr key={i}>
                    {queryResult.dimensions.map((d) => <td key={d}>{String(row[d])}</td>)}
                    <td>{row.value}</td>
                    <td>{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
