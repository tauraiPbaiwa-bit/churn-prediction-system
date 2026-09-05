"""
Explainability utilities: SHAP values for tree-based models (primarily XGBoost),
with graceful fallback if SHAP computation is too slow/unavailable for a given model.
"""
import numpy as np
import shap


def compute_shap_summary(model, X_sample, feature_names: list, model_name: str, max_rows: int = 200) -> dict:
    """
    Compute mean absolute SHAP value per feature (global importance) on a sample
    of rows, to keep computation practical for a classroom project.
    """
    try:
        sample = X_sample.sample(n=min(max_rows, len(X_sample)), random_state=42)

        if model_name in ("xgboost", "random_forest"):
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(sample)
        else:
            explainer = shap.LinearExplainer(model, sample)
            shap_values = explainer.shap_values(sample)

        # Binary classifiers can return a list [class0, class1] or a single array
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        shap_values = np.array(shap_values)
        if shap_values.ndim == 3:
            shap_values = shap_values[:, :, 1]

        mean_abs = np.abs(shap_values).mean(axis=0)
        pairs = sorted(zip(feature_names, mean_abs), key=lambda x: x[1], reverse=True)

        return {
            "available": True,
            "summary": [{"feature": f, "mean_abs_shap": round(float(v), 5)} for f, v in pairs],
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}
