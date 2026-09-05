"""
OLAP / multidimensional analysis endpoints: dataset summary, segmentation,
and custom dimension/measure queries.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.database import history_collection
from app.models.schemas import OlapQuery
from app.ml import olap as olap_engine
from app.routers.datasets import get_dataset_dataframe

router = APIRouter(prefix="/api/olap", tags=["OLAP / Analytics"])


@router.get("/{dataset_id}/overview")
def overview(dataset_id: str):
    df, doc = get_dataset_dataframe(dataset_id)
    return olap_engine.dataset_overview(df, doc.get("churn_column"))


@router.get("/{dataset_id}/segments")
def segments(dataset_id: str):
    df, doc = get_dataset_dataframe(dataset_id)
    return olap_engine.segment_customers(df, doc.get("churn_column"))


@router.post("/query")
def custom_query(query: OlapQuery):
    df, doc = get_dataset_dataframe(query.dataset_id)
    try:
        result = olap_engine.multidimensional_query(df, query.dimensions, query.measure, doc.get("churn_column"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    history_collection.insert_one({
        "type": "olap_query",
        "dataset_id": query.dataset_id,
        "dimensions": query.dimensions,
        "measure": query.measure,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "result_count": len(result),
    })

    return {"dimensions": query.dimensions, "measure": query.measure, "result": result}
