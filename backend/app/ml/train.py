"""
ML pipeline stage: train/test split -> train candidate models -> evaluate -> select best.

Models compared: XGBoost (primary), Logistic Regression, Random Forest.
"""
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve
)
from xgboost import XGBClassifier


def get_candidate_models(random_state: int = 42, scale_pos_weight: float = 1.0):
    return {
        "xgboost": XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=random_state,
            n_jobs=-1,
            scale_pos_weight=scale_pos_weight,
        ),
        "logistic_regression": LogisticRegression(
            max_iter=1000, random_state=random_state, class_weight="balanced"
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=10, random_state=random_state, n_jobs=-1,
            class_weight="balanced",
        ),
    }


def evaluate_model(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred).tolist()
    fpr, tpr, _ = roc_curve(y_test, y_proba)

    # Subsample ROC curve points to keep MongoDB documents small
    step = max(1, len(fpr) // 50)
    roc_points = [{"fpr": float(fpr[i]), "tpr": float(tpr[i])} for i in range(0, len(fpr), step)]

    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "confusion_matrix": cm,
        "roc_curve": roc_points,
    }


def train_and_compare(X, y, test_size: float = 0.2, random_state: int = 42):
    """
    Trains all candidate models, evaluates each, and selects the best by a composite
    of recall + F1 + ROC-AUC (never by accuracy alone, which favors the majority class).

    Returns dict: {
        "results": {model_name: {metrics...}},
        "trained_models": {model_name: fitted_estimator},
        "best_model_name": str,
        "X_test": DataFrame, "y_test": Series  (kept for downstream SHAP/analysis)
    }
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Handle class imbalance: XGBoost uses scale_pos_weight (ratio of negatives to positives),
    # LogisticRegression/RandomForest use class_weight="balanced" (set in get_candidate_models).
    neg, pos = int((y_train == 0).sum()), int((y_train == 1).sum())
    scale_pos_weight = neg / pos if pos > 0 else 1.0

    candidates = get_candidate_models(random_state, scale_pos_weight=scale_pos_weight)
    results = {}
    trained_models = {}

    for name, model in candidates.items():
        model.fit(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        # Composite score balances recall, F1 and ROC-AUC so a model that only
        # predicts the majority class (high accuracy, zero recall) is never selected.
        metrics["composite_score"] = round(
            (metrics["recall"] + metrics["f1_score"] + metrics["roc_auc"]) / 3, 4
        )
        results[name] = metrics
        trained_models[name] = model

    best_model_name = max(results.keys(), key=lambda k: results[k]["composite_score"])

    return {
        "results": results,
        "trained_models": trained_models,
        "best_model_name": best_model_name,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
    }


def get_feature_importance(model, feature_names: list, model_name: str) -> list[dict]:
    """Extract feature importance (works for XGBoost & RandomForest; coefficients for LogisticRegression)."""
    if model_name == "logistic_regression":
        importances = np.abs(model.coef_[0])
    else:
        importances = model.feature_importances_

    pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    total = float(sum(v for _, v in pairs)) or 1.0
    return [
        {"feature": name, "importance": round(float(val), 5), "importance_pct": round(float(val) / total * 100, 2)}
        for name, val in pairs
    ]
