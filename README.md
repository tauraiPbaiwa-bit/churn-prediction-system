# Customer Churn Prediction System

A full-stack, production-style **Customer Churn Prediction System** built as a third-year
Computer Science academic project. It lets you upload real-world customer datasets, cleans
and analyzes them (including an OLAP-style multidimensional analysis layer), trains and
compares XGBoost / Logistic Regression / Random Forest models, explains predictions with
SHAP, and serves individual + batch churn predictions through a React dashboard.

---

## 1. Architecture Overview

```
churn-prediction-system/
├── backend/                     FastAPI application
│   ├── app/
│   │   ├── main.py              App entrypoint, CORS, error handling
│   │   ├── config.py            Environment-based settings
│   │   ├── database.py          MongoDB connection & collections
│   │   ├── models/
│   │   │   └── schemas.py       Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── datasets.py      Upload / list / preview / delete datasets
│   │   │   ├── olap.py          OLAP summary, segmentation, custom queries
│   │   │   ├── training.py      Train & compare ML models
│   │   │   └── predictions.py   Individual & batch prediction, history
│   │   ├── ml/
│   │   │   ├── data_processing.py   Validation, cleaning, target detection
│   │   │   ├── feature_engineering.py Encoding & scaling
│   │   │   ├── olap.py              Multidimensional aggregation engine
│   │   │   ├── train.py             Model training + evaluation + selection
│   │   │   ├── explain.py           SHAP explainability
│   │   │   ├── predict.py           Prediction + risk classification
│   │   │   └── persistence.py       Joblib model save/load
│   │   └── utils/
│   │       └── security.py      Upload validation & input sanitization
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                    React + Vite dashboard
│   └── src/
│       ├── api/client.js        Axios API client
│       ├── pages/                10 dashboard pages (see below)
│       ├── components/           Sidebar, shared UI widgets
│       └── App.jsx / main.jsx
│
└── README.md (this file)
```

### ML Pipeline (per training run)
```
Upload (CSV/Excel)
   → Validate & Clean (missing values, duplicates, type coercion, churn-column detection)
   → Store cleaned records in MongoDB
   → Feature Engineering (label encoding + standard scaling)
   → Train/Test Split
   → Train XGBoost, Logistic Regression, Random Forest
   → Evaluate (Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix, ROC Curve)
   → Select best model by ROC-AUC
   → Compute Feature Importance + SHAP summary
   → Persist model bundle (model + encoders + scaler) via Joblib
   → Store metrics & metadata in MongoDB
```

### Dashboard Pages (maps to the 10 requested features)
1. **Dataset Upload & Management** — upload, list, preview, delete datasets
2. **OLAP Summary** — dataset overview + custom multidimensional slice/dice queries
3. **Churn Distribution & Customer Analytics** — pie/bar charts across segments
4. **Model Training** — trigger the full ML pipeline
5–7. **Model Comparison / XGBoost Metrics / Feature Importance & SHAP** — combined page with tables + charts
8. **Individual Prediction** — single customer form → churn probability + risk tier
9. **Batch Prediction** — predict churn across an entire dataset
10. **Prediction History** — log of all past predictions

---

## 2. Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB running locally (or a MongoDB Atlas connection string)

Install MongoDB locally (Ubuntu example) or use Docker:
```bash
docker run -d --name churn-mongo -p 27017:27017 mongo:7
```

---

## 3. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # edit MONGO_URI / APP_SECRET_KEY if needed

uvicorn app.main:app --reload --port 8000
```

- API base URL: `http://localhost:8000`
- Interactive API docs (Swagger): `http://localhost:8000/docs`
- Health check: `GET http://localhost:8000/api/health`

---

## 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

- Dashboard: `http://localhost:5173`
- Vite is pre-configured to proxy `/api/*` requests to `http://localhost:8000`.

For production build:
```bash
npm run build
npm run preview
```

---

## 5. Using the System (typical workflow)

1. **Upload** a churn dataset (CSV/XLSX) — e.g. the popular Telco Customer Churn dataset.
   The system auto-detects the churn column (`Churn`, `Exited`, `Attrition`, etc.), cleans
   missing values, coerces numeric columns, removes duplicates, and stores everything in
   MongoDB.
2. Go to **OLAP Summary** to see totals and run custom dimension/measure queries
   (e.g. churn rate by `Contract` × `PaymentMethod`).
3. Go to **Churn Analytics** for visual segment breakdowns.
4. Go to **Model Training**, select the dataset, click **Train & Compare Models**.
   This trains XGBoost, Logistic Regression and Random Forest, evaluates all three, and
   saves the best one.
5. Go to **Model Comparison & SHAP** to inspect metrics, confusion matrix, ROC curve,
   feature importance and SHAP values.
6. Use **Individual Prediction** to score a single customer, or **Batch Prediction** to
   score an entire dataset at once.
7. Check **Prediction History** for a full log.

---

## 6. API Reference (summary)

| Method | Endpoint                              | Description                          |
|--------|----------------------------------------|---------------------------------------|
| POST   | `/api/datasets/upload`                | Upload & clean a CSV/Excel file       |
| GET    | `/api/datasets/`                      | List datasets                         |
| GET    | `/api/datasets/{id}`                  | Dataset metadata                      |
| GET    | `/api/datasets/{id}/preview`          | Preview first N rows                  |
| DELETE | `/api/datasets/{id}`                  | Delete a dataset                      |
| GET    | `/api/olap/{id}/overview`             | High-level OLAP summary               |
| GET    | `/api/olap/{id}/segments`             | Pre-built segment breakdowns          |
| POST   | `/api/olap/query`                     | Custom dimension/measure OLAP query   |
| POST   | `/api/models/train`                   | Train & compare models                |
| GET    | `/api/models/`                        | List trained model runs               |
| GET    | `/api/models/{id}`                    | Model run details/metrics             |
| POST   | `/api/predictions/individual`         | Predict for one customer              |
| POST   | `/api/predictions/batch`              | Predict for an entire dataset         |
| GET    | `/api/predictions/history`            | Prediction history                    |

Full interactive documentation (with request/response schemas) is auto-generated by
FastAPI at `/docs` (Swagger UI) and `/redoc`.

---

## 7. Security Notes

- Uploads are restricted to `.csv/.xlsx/.xls`, size-limited (`MAX_UPLOAD_SIZE_MB`), and
  filenames are sanitized before storage.
- Free-text prediction inputs are sanitized to strip characters commonly used in
  injection attacks.
- Secrets (Mongo URI, app secret key) are loaded from environment variables via `.env`
  — never hardcoded.
- A global FastAPI exception handler prevents raw stack traces from leaking to clients.

This is an academic-project-level security baseline, not a hardened production
deployment (no auth/rate-limiting layer is included — see "Future Work" below).

---

## 8. Model Persistence

Each training run saves a single Joblib bundle per model to `backend/saved_models/`,
containing the fitted estimator, label encoders, scaler, and feature column list, so
predictions always apply identical preprocessing to new data.

---

## 9. Future Work / Extensions

- User authentication & role-based access
- Scheduled retraining / model versioning & rollback
- Drift detection on incoming batch predictions
- Dockerized deployment (`docker-compose` for API + MongoDB + frontend)
- Hyperparameter tuning (GridSearch/Optuna) for XGBoost

---

## 10. Tech Stack Summary

| Layer          | Technology                                   |
|-----------------|-----------------------------------------------|
| ML Models       | XGBoost, Logistic Regression, Random Forest (scikit-learn) |
| Explainability  | SHAP, native feature importance               |
| Backend         | FastAPI, Pydantic                             |
| Database        | MongoDB (PyMongo)                             |
| Model Storage   | Joblib                                        |
| Frontend        | React 18, Vite, Recharts, Axios               |
| Data Processing | Pandas, NumPy, scikit-learn                   |
