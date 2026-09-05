import { useEffect, useState } from "react";
import { uploadDataset, listDatasets, deleteDataset, previewDataset } from "../api/client";
import { ErrorBanner, SuccessBanner } from "../components/Common";
import { useAppCtx } from "../AppContext";

export default function UploadPage() {
  const [datasets, setDatasets] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [preview, setPreview] = useState(null);
  const { datasetId, selectDataset } = useAppCtx();

  const refresh = async () => {
    const res = await listDatasets();
    setDatasets(res.data.datasets);
  };

  useEffect(() => { refresh(); }, []);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const res = await uploadDataset(file);
      setSuccess(`Uploaded "${res.data.dataset.filename}" — ${res.data.dataset.rows} rows cleaned. Churn column: ${res.data.dataset.churn_column || "not auto-detected"}`);
      selectDataset(res.data.dataset.dataset_id);
      setFile(null);
      refresh();
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    await deleteDataset(id);
    if (datasetId === id) selectDataset("");
    refresh();
  };

  const handlePreview = async (id) => {
    selectDataset(id);
    const res = await previewDataset(id, 10);
    setPreview(res.data);
  };

  return (
    <div>
      <div className="page-title">Dataset Upload & Management</div>
      <div className="page-subtitle">Upload real-world CSV/Excel churn datasets. Files are validated, cleaned and stored in MongoDB automatically.</div>

      <div className="card">
        <ErrorBanner message={error} />
        <SuccessBanner message={success} />
        <div className="form-row">
          <label>CSV / Excel file (.csv, .xlsx, .xls)</label>
          <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setFile(e.target.files[0])} />
        </div>
        <button className="btn" onClick={handleUpload} disabled={!file || loading}>
          {loading ? "Uploading & Cleaning..." : "Upload Dataset"}
        </button>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Your Datasets</h3>
        {datasets.length === 0 && <div className="empty-state">No datasets uploaded yet.</div>}
        {datasets.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Filename</th><th>Rows</th><th>Cols</th><th>Churn Column</th><th>Uploaded</th><th></th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((d) => (
                <tr key={d.dataset_id} style={{ background: d.dataset_id === datasetId ? "#1d2740" : "transparent" }}>
                  <td>{d.filename}</td>
                  <td>{d.rows}</td>
                  <td>{d.columns}</td>
                  <td>{d.churn_column || "—"}</td>
                  <td>{new Date(d.uploaded_at).toLocaleString()}</td>
                  <td style={{ display: "flex", gap: 6 }}>
                    <button className="btn secondary" onClick={() => handlePreview(d.dataset_id)}>Select / Preview</button>
                    <button className="btn danger" onClick={() => handleDelete(d.dataset_id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {preview && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Preview (first 10 rows)</h3>
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>{preview.columns.map((c) => <th key={c}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {preview.rows.map((r, i) => (
                  <tr key={i}>{preview.columns.map((c) => <td key={c}>{String(r[c])}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
