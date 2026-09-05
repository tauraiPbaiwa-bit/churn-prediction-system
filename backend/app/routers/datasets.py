"""
Dataset upload, validation, cleaning, listing and retrieval endpoints.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd

from app.config import settings
from app.database import datasets_collection, customers_collection
from app.utils.security import validate_upload_file, validate_file_size, sanitize_filename
from app.ml.data_processing import (
    load_dataframe, detect_churn_column, basic_validation_report, clean_dataframe
)

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a CSV/Excel file: validate -> clean -> detect churn column -> persist to MongoDB."""
    validate_upload_file(file, settings.max_upload_size_mb)
    raw_bytes = await file.read()
    validate_file_size(len(raw_bytes), settings.max_upload_size_mb)

    try:
        df_raw = load_dataframe(raw_bytes, file.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {exc}")

    raw_report = basic_validation_report(df_raw)
    churn_col = detect_churn_column(df_raw)

    try:
        df_clean = clean_dataframe(df_raw, churn_col)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to clean data: {exc}")

    dataset_id = str(uuid.uuid4())
    safe_name = sanitize_filename(file.filename)

    dataset_doc = {
        "dataset_id": dataset_id,
        "filename": safe_name,
        "original_filename": file.filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "rows": int(df_clean.shape[0]),
        "columns": int(df_clean.shape[1]),
        "churn_column": churn_col,
        "column_types": {c: str(df_clean[c].dtype) for c in df_clean.columns},
        "missing_values_before_cleaning": raw_report["missing_values"],
        "duplicate_rows_removed": raw_report["duplicate_rows"],
        "column_list": list(df_clean.columns),
    }
    datasets_collection.insert_one(dataset_doc)

    # Store cleaned records (each row tagged with dataset_id) for later OLAP/ML use
    records = df_clean.to_dict(orient="records")
    for r in records:
        r["dataset_id"] = dataset_id
    if records:
        customers_collection.insert_many(records)

    dataset_doc.pop("_id", None)
    return {"message": "Dataset uploaded, validated and cleaned successfully.", "dataset": dataset_doc}


@router.get("/")
def list_datasets():
    docs = list(datasets_collection.find({}, {"_id": 0}).sort("uploaded_at", -1))
    return {"datasets": docs}


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str):
    doc = datasets_collection.find_one({"dataset_id": dataset_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return doc


@router.get("/{dataset_id}/preview")
def preview_dataset(dataset_id: str, limit: int = 20):
    doc = datasets_collection.find_one({"dataset_id": dataset_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    rows = list(customers_collection.find({"dataset_id": dataset_id}, {"_id": 0}).limit(limit))
    return {"columns": doc["column_list"], "rows": rows}


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str):
    result = datasets_collection.delete_one({"dataset_id": dataset_id})
    customers_collection.delete_many({"dataset_id": dataset_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return {"message": "Dataset deleted."}


def get_dataset_dataframe(dataset_id: str) -> pd.DataFrame:
    """Helper used by other routers to load a dataset's cleaned records as a DataFrame."""
    doc = datasets_collection.find_one({"dataset_id": dataset_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    rows = list(customers_collection.find({"dataset_id": dataset_id}, {"_id": 0}))
    if not rows:
        raise HTTPException(status_code=400, detail="Dataset has no stored records.")
    df = pd.DataFrame(rows)
    if "dataset_id" in df.columns:
        df = df.drop(columns=["dataset_id"])
    return df, doc
