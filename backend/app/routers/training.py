"""
Model training endpoints: run the full ML pipeline (feature engineering ->
train/test split -> train XGBoost/LogReg/RandomForest -> evaluate -> select best
-> persist via joblib -> store metrics + SHAP summary in MongoDB).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import models_collection
from app.models.schemas import TrainRequest
from app.routers.datasets import get_dataset_dataframe
from app.ml.feature_engineering import build_features
from app.ml.train import train_and_compare, get_feature_importance
from app.ml.explain import compute_shap_summary
from app.ml.persistence import save_model_bundle

router = APIRouter(prefix="/api/models", tags=["Model Training"])


@router.post("/train")
def train_models(req: TrainRequest):
    df, doc = get_dataset_dataframe(req.dataset_id)
    target_col = req.target_column or doc.get("churn_column")

    if not target_col or target_col not in df.columns:
        raise HTTPException(
            status_code=400,
            detail="Could not determine churn/target column. Please specify target_column explicitly.",
        )

    if df[target_col].nunique() != 2:
        raise HTTPException(status_code=400, detail="Target column must be binary for churn classification.")

    X, y, encoders, scaler, feature_columns = build_features(df, target_col)

    try:
        result = train_and_compare(X, y, test_size=req.test_size, random_state=req.random_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Training failed: {exc}")

    best_name = result["best_model_name"]
    best_model = result["trained_models"][best_name]

    model_id = str(uuid.uuid4())
    save_model_bundle(model_id, {
        "model": best_model,
        "model_name": best_name,
        "encoders": encoders,
        "scaler": scaler,
        "feature_columns": feature_columns,
        "target_column": target_col,
        "dataset_id": req.dataset_id,
    })

    feature_importance = get_feature_importance(best_model, feature_columns, best_name)
    shap_summary = compute_shap_summary(best_model, result["X_test"], feature_columns, best_name)

    model_doc = {
        "model_id": model_id,
        "dataset_id": req.dataset_id,
        "target_column": target_col,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "best_model_name": best_name,
        "all_results": result["results"],          # metrics for xgboost / logreg / rf
        "feature_columns": feature_columns,
        "feature_importance": feature_importance,
        "shap_summary": shap_summary,
        "train_rows": int(len(result["X_train"])),
        "test_rows": int(len(result["X_test"])),
    }
    models_collection.insert_one(dict(model_doc))
    model_doc.pop("_id", None)

    return {"message": "Training complete.", "model": model_doc}


@router.get("/")
def list_models():
    docs = list(models_collection.find({}, {"_id": 0}).sort("trained_at", -1))
    return {"models": docs}


@router.get("/{model_id}")
def get_model(model_id: str):
    doc = models_collection.find_one({"model_id": model_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Model not found.")
    return doc
