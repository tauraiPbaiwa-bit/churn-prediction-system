"""
Prediction endpoints: individual customer prediction and batch prediction from
an uploaded dataset, plus prediction history retrieval.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import predictions_collection, models_collection
from app.models.schemas import IndividualPredictionRequest, BatchPredictionRequest
from app.ml.persistence import load_model_bundle
from app.ml.predict import predict_single, predict_batch
from app.routers.datasets import get_dataset_dataframe
from app.utils.security import sanitize_string

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])
predict_router = APIRouter(tags=["Predictions"])


def _run_individual_prediction(req: IndividualPredictionRequest) -> dict:
    try:
        bundle = load_model_bundle(req.model_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model not found.")

    clean_data = {
        k: (sanitize_string(v) if isinstance(v, str) else v) for k, v in req.customer_data.items()
    }

    try:
        result = predict_single(bundle, clean_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}")

    record = {
        "prediction_id": str(uuid.uuid4()),
        "type": "individual",
        "model_id": req.model_id,
        "input": clean_data,
        "result": result,
        "model_name": bundle.get("model_name"),
        "predicted_at": datetime.now(timezone.utc).isoformat(),
    }
    predictions_collection.insert_one(dict(record))
    record.pop("_id", None)
    return record


@router.post("/individual")
def predict_individual(req: IndividualPredictionRequest):
    return _run_individual_prediction(req)


@predict_router.post("/api/predict")
def predict(req: IndividualPredictionRequest):
    """Primary endpoint used by the Opal frontend for a single customer prediction."""
    record = _run_individual_prediction(req)
    model_doc = models_collection.find_one({"model_id": req.model_id}, {"_id": 0})
    return {
        **record["result"],
        "model_id": req.model_id,
        "model_name": record.get("model_name"),
        "model_trained_at": model_doc.get("trained_at") if model_doc else None,
        "prediction_id": record["prediction_id"],
    }


@router.post("/batch")
def predict_batch_endpoint(req: BatchPredictionRequest):
    try:
        bundle = load_model_bundle(req.model_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model not found.")

    df, _doc = get_dataset_dataframe(req.dataset_id)
    target_col = bundle.get("target_column")
    if target_col in df.columns:
        df = df.drop(columns=[target_col])

    try:
        result_df = predict_batch(bundle, df)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Batch prediction failed: {exc}")

    summary = {
        "total_customers": int(len(result_df)),
        "predicted_churn": int(result_df["churn_prediction"].sum()),
        "high_risk": int((result_df["risk_tier"] == "High").sum()),
        "medium_risk": int((result_df["risk_tier"] == "Medium").sum()),
        "low_risk": int((result_df["risk_tier"] == "Low").sum()),
    }

    batch_id = str(uuid.uuid4())
    record = {
        "prediction_id": batch_id,
        "type": "batch",
        "model_id": req.model_id,
        "dataset_id": req.dataset_id,
        "summary": summary,
        "predicted_at": datetime.now(timezone.utc).isoformat(),
        "sample_results": result_df.head(50).to_dict(orient="records"),
    }
    predictions_collection.insert_one(dict(record))
    record.pop("_id", None)
    return record


@router.get("/history")
def prediction_history(limit: int = 50):
    docs = list(predictions_collection.find({}, {"_id": 0}).sort("predicted_at", -1).limit(limit))
    return {"predictions": docs}


@router.get("/{prediction_id}")
def get_prediction(prediction_id: str):
    doc = predictions_collection.find_one({"prediction_id": prediction_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Prediction not found.")
    return doc
