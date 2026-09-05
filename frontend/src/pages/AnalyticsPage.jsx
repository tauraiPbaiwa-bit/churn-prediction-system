import { useEffect, useState } from "react";
import { listDatasets, getSegments, getOverview } from "../api/client";
import { DatasetPicker } from "../components/Common";
import { useAppCtx } from "../AppContext";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from "recharts";

const COLORS = ["#5b8cff", "#38d9a9", "#ffb84d", "#ff6b6b", "#a78bfa", "#f472b6"];

export default function AnalyticsPage() {
  const { datasetId, selectDataset } = useAppCtx();
  const [datasets, setDatasets] = useState([]);
  const [segments, setSegments] = useState(null);
  const [overview, setOverview] = useState(null);

  useEffect(() => { listDatasets().then((r) => setDatasets(r.data.datasets)); }, []);

  useEffect(() => {
    if (!datasetId) { setSegments(null); setOverview(null); return; }
    getSegments(datasetId).then((r) => setSegments(r.data));
    getOverview(datasetId).then((r) => setOverview(r.data));
  }, [datasetId]);

  const pieData = overview
    ? [
        { name: "Churned", value: overview.churned_customers || 0 },
        { name: "Retained", value: overview.retained_customers || 0 },
      ]
    : [];

  const renderBarSegment = (title, dimKey, data) => {
    if (!data) return null;
    const xKey = Object.keys(data[0] || {}).find((k) => k !== "value" && k !== "count");
    return (
      <div className="card" key={dimKey}>
        <h4 style={{ marginTop: 0 }}>{title}</h4>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a3552" />
            <XAxis dataKey={xKey} stroke="#93a0bd" fontSize={12} />
            <YAxis stroke="#93a0bd" fontSize={12} />
            <Tooltip contentStyle={{ background: "#161d2e", border: "1px solid #2a3552" }} />
            <Bar dataKey="value" fill="#5b8cff" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div>
      <div className="page-title">Churn Distribution & Customer Analytics</div>
      <div className="page-subtitle">Visual breakdown of churn across key customer segments.</div>

      <div className="card">
        <DatasetPicker datasets={datasets} value={datasetId} onChange={selectDataset} />
      </div>

      {overview && (
        <div className="card">
          <h4 style={{ marginTop: 0 }}>Overall Churn vs Retained</h4>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={100} label>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Legend />
              <Tooltip contentStyle={{ background: "#161d2e", border: "1px solid #2a3552" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {segments && (
        <div className="grid grid-2">
          {Object.entries(segments).map(([key, data]) => renderBarSegment(`Churn rate by ${key}`, key, data))}
        </div>
      )}

      {!segments && <div className="empty-state">Select a dataset to view analytics.</div>}
    </div>
  );
}
