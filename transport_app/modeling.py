from __future__ import annotations

import json
import math
import pickle
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from transport_app.config import MODELS_DIR
from transport_app.features import FEATURE_ORDER, feature_vector
from transport_app.storage import get_connection, init_db

MODEL_PATH = MODELS_DIR / "delay_model.pkl"
METRICS_PATH = MODELS_DIR / "delay_model_metrics.json"
DELAY_THRESHOLD_MINUTES = 10.0


def _ensure_dirs() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


def _default_regressor() -> Any:
    """
    Prefer XGBoost/LightGBM if available, otherwise fall back to GradientBoostingRegressor.
    """
    try:
        from xgboost import XGBRegressor

        return XGBRegressor(
            n_estimators=120,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
    except ImportError:
        try:
            from lightgbm import LGBMRegressor

            return LGBMRegressor(
                n_estimators=180,
                max_depth=-1,
                learning_rate=0.08,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            )
        except ImportError:
            from sklearn.ensemble import GradientBoostingRegressor

            return GradientBoostingRegressor(random_state=42)


def load_delay_model() -> Any | None:
    _ensure_dirs()
    if not MODEL_PATH.exists():
        return None
    with MODEL_PATH.open("rb") as f:
        return pickle.load(f)


def _save_delay_model(model: Any) -> None:
    _ensure_dirs()
    with MODEL_PATH.open("wb") as f:
        pickle.dump(model, f)


def _save_metrics(payload: dict[str, Any]) -> None:
    _ensure_dirs()
    METRICS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _rows_from_db(limit: int = 2000) -> Iterable[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT route_id, response_json FROM route_evaluations ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    for row in rows:
        try:
            payload = json.loads(row["response_json"])
        except json.JSONDecodeError:
            continue
        yield {"route_id": row["route_id"], "response": payload}


def _features_from_response(record: dict[str, Any]) -> tuple[list[float], float] | None:
    response = record.get("response", {})
    legs = response.get("legs", [])
    if not isinstance(legs, list):
        return None

    alerts_count = float(sum(leg.get("matched_alerts", 0) for leg in legs))
    vehicle_density = float(
        sum(leg.get("active_vehicles", 0) for leg in legs) / max(len(legs), 1)
    )
    time_of_day_minutes = 12 * 60  # not recorded in DB; fallback
    num_legs = float(len(legs))
    num_transfers = float(max(len(legs) - 1, 0))
    history_delay_mean = float(response.get("expected_delay_minutes", 0))
    history_delay_max = history_delay_mean
    features = {
        "alerts_count": alerts_count,
        "vehicle_density": vehicle_density,
        "time_of_day_minutes": float(time_of_day_minutes),
        "num_legs": num_legs,
        "num_transfers": num_transfers,
        "history_delay_mean": history_delay_mean,
        "history_delay_max": history_delay_max,
    }
    target = float(response.get("expected_delay_minutes", 0))
    return feature_vector(features), target


def train_delay_model(limit: int = 2000) -> dict[str, float] | None:
    """
    Train a regression model from stored route_evaluations history.
    Returns evaluation metrics; saves the fitted model to disk.
    """
    rows = list(_rows_from_db(limit))
    dataset: list[tuple[list[float], float]] = []
    for row in rows:
        entry = _features_from_response(row)
        if entry:
            dataset.append(entry)

    if len(dataset) < 10:
        return None

    X = np.array([item[0] for item in dataset], dtype=float)
    y = np.array([item[1] for item in dataset], dtype=float)

    try:
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    except ImportError:
        # If sklearn is missing just skip training 
        return None

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = _default_regressor()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(math.sqrt(mean_squared_error(y_test, preds)))
    r2 = float(r2_score(y_test, preds))

    _save_delay_model(model)
    metrics = {"mae": mae, "rmse": rmse, "r2": r2, "train_size": len(X_train), "test_size": len(X_test)}
    _save_metrics(metrics)
    return metrics


def predict_delay(features: dict[str, float]) -> tuple[float, float]:
    """
    Returns (predicted_delay_minutes, probability_delay_over_threshold).
    If no trained model exists, falls back to heurestic based on feature values. 
    """
    model = load_delay_model()
    vector = np.array([feature_vector(features)], dtype=float)

    if model is not None:
        delay_minutes = float(model.predict(vector)[0])
    else:
        # Heuristic fallback when no model is trained yet.
        delay_minutes = (
            3 * features.get("alerts_count", 0)
            + 1.5 * features.get("num_transfers", 0)
            + 0.5 * features.get("history_delay_mean", 0)
        )

    # Logistic mapping to probability a delay exceeds threshold.
    prob = 1 / (1 + math.exp(-((delay_minutes - DELAY_THRESHOLD_MINUTES) / 3)))
    return max(0.0, delay_minutes), float(min(max(prob, 0.0), 1.0))
