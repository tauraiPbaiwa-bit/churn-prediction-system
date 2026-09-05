"""
Prediction stage: apply saved model bundle to new data (individual or batch)
and classify churn probability into risk tiers.
"""
import pandas as pd
from app.ml.feature_engineering import transform_new_data

RECOMMENDATIONS = {
    "High": "Immediate retention action recommended: reach out with a loyalty offer, "
            "discount, or contract upgrade before the customer churns.",
    "Medium": "Proactively engage this customer with a satisfaction check-in or "
              "targeted service review to reduce churn risk.",
    "Low": "Customer appears stable. Continue standard engagement and monitoring.",
}


def risk_level(probability: float) -> str:
    if probability >= 0.7:
        return "High"
    if probability >= 0.4:
        return "Medium"
    return "Low"


def predict_single(bundle: dict, customer_data: dict) -> dict:
    df = pd.DataFrame([customer_data])
    X = transform_new_data(df, bundle["encoders"], bundle["scaler"], bundle["feature_columns"])
    model = bundle["model"]
    proba = float(model.predict_proba(X)[0][1])
    pred = int(proba >= 0.5)
    level = risk_level(proba)
    return {
        "prediction": "Churn" if pred == 1 else "No Churn",
        "churn_prediction": pred,
        "churn_probability": round(proba, 4),
        "retention_probability": round(1 - proba, 4),
        "risk_level": level,
        "recommendation": RECOMMENDATIONS[level],
    }


def predict_batch(bundle: dict, df: pd.DataFrame) -> pd.DataFrame:
    X = transform_new_data(df, bundle["encoders"], bundle["scaler"], bundle["feature_columns"])
    model = bundle["model"]
    probas = model.predict_proba(X)[:, 1]
    preds = (probas >= 0.5).astype(int)

    result = df.copy()
    result["churn_prediction"] = preds
    result["churn_probability"] = probas.round(4)
    result["risk_tier"] = [risk_level(p) for p in probas]
    return result
