import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 60000,
});

// Datasets
export const uploadDataset = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/datasets/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
export const listDatasets = () => api.get("/datasets/");
export const getDataset = (id) => api.get(`/datasets/${id}`);
export const previewDataset = (id, limit = 20) => api.get(`/datasets/${id}/preview?limit=${limit}`);
export const deleteDataset = (id) => api.delete(`/datasets/${id}`);

// OLAP
export const getOverview = (id) => api.get(`/olap/${id}/overview`);
export const getSegments = (id) => api.get(`/olap/${id}/segments`);
export const runOlapQuery = (payload) => api.post(`/olap/query`, payload);

// Training
export const trainModels = (payload) => api.post(`/models/train`, payload);
export const listModels = () => api.get(`/models/`);
export const getModel = (id) => api.get(`/models/${id}`);

// Predictions
export const predict = (payload) => api.post(`/predict`, payload);
export const predictIndividual = (payload) => api.post(`/predictions/individual`, payload);
export const predictBatch = (payload) => api.post(`/predictions/batch`, payload);
export const predictionHistory = (limit = 50) => api.get(`/predictions/history?limit=${limit}`);

export default api;
