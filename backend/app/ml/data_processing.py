"""
Data ingestion, validation, cleaning and preprocessing utilities.

Pipeline stage 1: raw file -> validated, cleaned pandas DataFrame
"""
import io
import re
import pandas as pd
import numpy as np

# Common churn-target naming patterns seen in real-world telecom/subscription datasets
CHURN_CANDIDATE_NAMES = [
    "churn", "churned", "is_churn", "customer_churn", "exited", "attrition", "cancelled", "canceled"
]


def load_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load CSV or Excel bytes into a DataFrame."""
    ext = filename.lower().split(".")[-1]
    if ext == "csv":
        df = pd.read_csv(io.BytesIO(file_bytes))
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    if df.empty:
        raise ValueError("Uploaded file contains no rows.")
    if df.shape[1] < 2:
        raise ValueError("Uploaded file must contain at least 2 columns.")
    return df


def detect_churn_column(df: pd.DataFrame) -> str | None:
    """Heuristically detect the churn/target column by name, else by binary-value heuristic."""
    for col in df.columns:
        if col.strip().lower() in CHURN_CANDIDATE_NAMES:
            return col

    # Fallback: look for a binary/boolean-like column whose name contains 'churn'
    for col in df.columns:
        if "churn" in col.strip().lower():
            return col

    # Fallback: any binary column with exactly 2 unique values incl. Yes/No, 0/1, True/False
    for col in df.columns:
        vals = set(str(v).strip().lower() for v in df[col].dropna().unique())
        if vals in [{"yes", "no"}, {"0", "1"}, {"true", "false"}]:
            return col

    return None


def basic_validation_report(df: pd.DataFrame) -> dict:
    """Produce a validation/summary report used by the API and stored with dataset metadata."""
    column_types = {c: str(df[c].dtype) for c in df.columns}
    missing_values = {c: int(df[c].isna().sum()) for c in df.columns}
    duplicate_rows = int(df.duplicated().sum())
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_types": column_types,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
    }


def clean_dataframe(df: pd.DataFrame, churn_column: str | None) -> pd.DataFrame:
    """
    Clean dataset:
    - Drop fully-empty columns/rows
    - Strip whitespace from string columns
    - Coerce numeric-looking object columns (e.g. TotalCharges with blanks) to numeric
    - Impute missing values (median for numeric, mode for categorical)
    - Drop duplicate rows
    - Normalize churn column to 0/1 if present
    """
    df = df.copy()

    # Drop entirely empty columns / rows
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")

    # Drop obvious ID columns (high cardinality unique identifiers) except churn column
    for col in df.columns:
        if col == churn_column:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique() == len(df):
            df = df.drop(columns=[col])

    # Strip whitespace on string/object columns, coerce numeric-looking strings
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"": np.nan, "nan": np.nan, "NaN": np.nan, "None": np.nan})
            coerced = pd.to_numeric(df[col], errors="coerce")
            # If most non-null values successfully convert, treat column as numeric
            if coerced.notna().sum() >= 0.9 * df[col].notna().sum() and df[col].notna().sum() > 0:
                df[col] = coerced

    # Impute missing values
    for col in df.columns:
        if df[col].isna().sum() == 0:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            mode = df[col].mode(dropna=True)
            fill_val = mode.iloc[0] if not mode.empty else "Unknown"
            df[col] = df[col].fillna(fill_val)

    # Drop duplicate rows
    df = df.drop_duplicates()

    # Normalize churn column to binary 0/1
    if churn_column and churn_column in df.columns:
        df[churn_column] = normalize_binary_column(df[churn_column])

    return df.reset_index(drop=True)


def normalize_binary_column(series: pd.Series) -> pd.Series:
    """Map common churn label formats to 0/1 integers."""
    mapping = {
        "yes": 1, "no": 0,
        "true": 1, "false": 0,
        "1": 1, "0": 0,
        "churned": 1, "retained": 0,
        "left": 1, "stayed": 0,
    }
    if pd.api.types.is_numeric_dtype(series):
        unique_vals = set(series.dropna().unique().tolist())
        if unique_vals <= {0, 1}:
            return series.astype(int)

    normalized = series.astype(str).str.strip().str.lower().map(mapping)
    if normalized.isna().any():
        # Fallback: encode top frequent value as 0 (majority/non-churn), rest as 1
        top_value = series.astype(str).str.strip().str.lower().mode().iloc[0]
        normalized = series.astype(str).str.strip().str.lower().apply(lambda v: 0 if v == top_value else 1)
    return normalized.astype(int)
