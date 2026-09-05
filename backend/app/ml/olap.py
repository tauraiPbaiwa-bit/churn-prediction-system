"""
Lightweight OLAP-style analysis layer over the cleaned customer dataset.

Implements multidimensional aggregation (roll-up/drill-down/slice-and-dice style
operations) using pandas groupby, since a full OLAP cube server is out of scope
for this academic project but the *concept* (dimensions, measures, aggregation)
is faithfully implemented.
"""
import pandas as pd
import numpy as np


MEASURE_FUNCS = {
    "count": lambda g, churn_col: int(len(g)),
    "churn_rate": lambda g, churn_col: round(float(g[churn_col].mean()) * 100, 2) if churn_col in g else None,
    "avg_tenure": lambda g, churn_col: round(float(g["tenure"].mean()), 2) if "tenure" in g.columns else None,
    "avg_monthly_charges": lambda g, churn_col: (
        round(float(g["MonthlyCharges"].mean()), 2) if "MonthlyCharges" in g.columns else None
    ),
}


def dataset_overview(df: pd.DataFrame, churn_col: str | None) -> dict:
    """High-level OLAP summary: total customers, churn rate, key dimension breakdowns."""
    overview = {
        "total_customers": int(len(df)),
        "total_features": int(df.shape[1]),
    }
    if churn_col and churn_col in df.columns:
        overview["overall_churn_rate"] = round(float(df[churn_col].mean()) * 100, 2)
        overview["churned_customers"] = int(df[churn_col].sum())
        overview["retained_customers"] = int(len(df) - df[churn_col].sum())
    return overview


def multidimensional_query(df: pd.DataFrame, dimensions: list[str], measure: str, churn_col: str | None) -> list[dict]:
    """
    Perform a group-by aggregation across the requested dimensions (columns),
    computing the requested measure for each combination — the core OLAP
    'slice and dice' operation.
    """
    missing = [d for d in dimensions if d not in df.columns]
    if missing:
        raise ValueError(f"Unknown dimension column(s): {missing}")
    if measure not in MEASURE_FUNCS:
        raise ValueError(f"Unknown measure '{measure}'. Options: {list(MEASURE_FUNCS.keys())}")

    func = MEASURE_FUNCS[measure]
    results = []
    grouped = df.groupby(dimensions, dropna=False)
    for key, group in grouped:
        keys = key if isinstance(key, tuple) else (key,)
        row = {dim: (val.item() if hasattr(val, "item") else val) for dim, val in zip(dimensions, keys)}
        row["value"] = func(group, churn_col)
        row["count"] = int(len(group))
        results.append(row)

    results.sort(key=lambda r: r["count"], reverse=True)
    return results


def segment_customers(df: pd.DataFrame, churn_col: str | None) -> dict:
    """
    Pre-built customer segmentation across common churn dimensions:
    contract type, tenure bucket, payment method, service type, churn status.
    Falls back gracefully if a column is absent from the dataset.
    """
    segments = {}

    if "tenure" in df.columns:
        bins = [-1, 6, 12, 24, 48, np.inf]
        labels = ["0-6 mo", "7-12 mo", "13-24 mo", "25-48 mo", "48+ mo"]
        df = df.copy()
        df["tenure_bucket"] = pd.cut(df["tenure"], bins=bins, labels=labels)
        segments["tenure"] = multidimensional_query(df, ["tenure_bucket"], "churn_rate", churn_col) \
            if churn_col else multidimensional_query(df, ["tenure_bucket"], "count", churn_col)

    for dim_col in ["Contract", "PaymentMethod", "InternetService", "gender"]:
        if dim_col in df.columns:
            measure = "churn_rate" if churn_col else "count"
            segments[dim_col] = multidimensional_query(df, [dim_col], measure, churn_col)

    return segments
