"""
Feature engineering: encodes categorical variables and scales numeric ones,
producing a model-ready feature matrix. Encoders/scalers are persisted alongside
the model so batch/individual predictions use identical transformations.
"""
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


def build_features(df: pd.DataFrame, target_col: str):
    """
    Split df into X (features) and y (target), encode categoricals with LabelEncoder,
    scale numeric columns with StandardScaler.

    Returns: X_scaled (DataFrame), y (Series), fitted_encoders (dict), fitted_scaler, feature_columns (list)
    """
    df = df.copy()
    y = df[target_col]
    X = df.drop(columns=[target_col])

    encoders = {}
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = le

    feature_columns = list(X.columns)

    scaler = StandardScaler()
    X_scaled_array = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled_array, columns=feature_columns, index=X.index)

    return X_scaled, y, encoders, scaler, feature_columns


def transform_new_data(df: pd.DataFrame, encoders: dict, scaler: StandardScaler, feature_columns: list) -> pd.DataFrame:
    """Apply previously-fitted encoders/scaler to new (individual or batch) input data."""
    df = df.copy()

    # Ensure all expected columns exist
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0

    df = df[feature_columns]

    for col, le in encoders.items():
        if col in df.columns:
            df[col] = df[col].astype(str).apply(
                lambda v: v if v in le.classes_ else le.classes_[0]
            )
            df[col] = le.transform(df[col])

    scaled_array = scaler.transform(df)
    return pd.DataFrame(scaled_array, columns=feature_columns, index=df.index)
