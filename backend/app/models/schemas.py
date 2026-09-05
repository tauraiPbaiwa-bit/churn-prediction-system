"""
Pydantic request/response schemas shared across routers.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetSummary(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    churn_column: Optional[str]
    uploaded_at: str
    column_types: Dict[str, str]
    missing_values: Dict[str, int]


class OlapQuery(BaseModel):
    dataset_id: str
    dimensions: List[str] = Field(..., description="Columns to group by, e.g. ['Contract', 'PaymentMethod']")
    measure: str = Field(default="churn_rate", description="churn_rate | count | avg_tenure | avg_monthly_charges")


class TrainRequest(BaseModel):
    dataset_id: str
    target_column: Optional[str] = None
    test_size: float = 0.2
    random_state: int = 42


class IndividualPredictionRequest(BaseModel):
    model_id: str
    customer_data: Dict[str, Any]


class BatchPredictionRequest(BaseModel):
    model_id: str
    dataset_id: str
