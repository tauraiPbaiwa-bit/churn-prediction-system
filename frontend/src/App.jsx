import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import { AppProvider } from "./AppContext.jsx";
import UploadPage from "./pages/UploadPage.jsx";
import OverviewPage from "./pages/OverviewPage.jsx";
import AnalyticsPage from "./pages/AnalyticsPage.jsx";
import TrainPage from "./pages/TrainPage.jsx";
import ModelsPage from "./pages/ModelsPage.jsx";
import PredictIndividualPage from "./pages/PredictIndividualPage.jsx";
import PredictBatchPage from "./pages/PredictBatchPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";

export default function App() {
  return (
    <AppProvider>
      <div className="app-shell">
        <Sidebar />
        <div className="main-content">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/overview" element={<OverviewPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/train" element={<TrainPage />} />
            <Route path="/models" element={<ModelsPage />} />
            <Route path="/predict/individual" element={<PredictIndividualPage />} />
            <Route path="/predict/batch" element={<PredictBatchPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </div>
      </div>
    </AppProvider>
  );
}
