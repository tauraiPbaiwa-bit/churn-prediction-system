"""
Model persistence: save/load trained models + their encoders/scaler/feature list
as a single joblib bundle, keyed by model_id.
"""
import os
import joblib
from app.config import settings


def save_model_bundle(model_id: str, bundle: dict) -> str:
    """bundle = {model, encoders, scaler, feature_columns, target_column, model_name}"""
    path = os.path.join(settings.model_dir, f"{model_id}.joblib")
    joblib.dump(bundle, path)
    return path


def load_model_bundle(model_id: str) -> dict:
    path = os.path.join(settings.model_dir, f"{model_id}.joblib")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No saved model found for model_id={model_id}")
    return joblib.load(path)
