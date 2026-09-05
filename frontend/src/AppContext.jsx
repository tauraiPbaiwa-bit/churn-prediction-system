import { createContext, useContext, useState } from "react";

const AppCtx = createContext(null);

export function AppProvider({ children }) {
  const [datasetId, setDatasetId] = useState(() => localStorage.getItem("last_dataset_id") || "");
  const [modelId, setModelId] = useState(() => localStorage.getItem("last_model_id") || "");

  const selectDataset = (id) => {
    setDatasetId(id);
    localStorage.setItem("last_dataset_id", id || "");
  };
  const selectModel = (id) => {
    setModelId(id);
    localStorage.setItem("last_model_id", id || "");
  };

  return (
    <AppCtx.Provider value={{ datasetId, selectDataset, modelId, selectModel }}>
      {children}
    </AppCtx.Provider>
  );
}

export const useAppCtx = () => useContext(AppCtx);
