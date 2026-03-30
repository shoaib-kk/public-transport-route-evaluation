from __future__ import annotations

from datetime import datetime
from statistics import mean
from typing import Iterable

from transport_app.feed_processing import AlertsSummary, VehiclePositionsSummary
from transport_app.models import RouteDefinition


def _minutes_since_midnight(time_str: str | None) -> int:
    if not time_str:
        return 12 * 60
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            parsed = datetime.strptime(time_str, fmt)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue
    return 12 * 60


def _history_delay_stats(history: Iterable[dict]) -> tuple[float, float]:
    delays = [
        entry["response"].get("expected_delay_minutes")
        for entry in history
        if isinstance(entry, dict)
        and isinstance(entry.get("response"), dict)
        and isinstance(entry["response"].get("expected_delay_minutes"), (int, float))
    ]
    if not delays:
        return 0.0, 0.0
    return float(mean(delays)), float(max(delays))


def extract_features(
    *,
    route: RouteDefinition,
    alerts: AlertsSummary,
    vehicles: VehiclePositionsSummary,
    history: Iterable[dict] | None = None,
) -> dict[str, float]:
    """
    Build a feature dictionary for model inference/training.
    """
    history_mean_delay, history_max_delay = _history_delay_stats(history or [])
    total_alerts = sum(alerts.route_alert_counts.get(leg.route_id, 0) for leg in route.legs)
    total_active_vehicles = sum(vehicles.route_vehicle_counts.get(leg.route_id, 0) for leg in route.legs)
    time_of_day_minutes = _minutes_since_midnight(route.planned_departure)

    return {
        "alerts_count": float(total_alerts),
        "vehicle_density": float(total_active_vehicles / max(len(route.legs), 1)),
        "time_of_day_minutes": float(time_of_day_minutes),
        "num_legs": float(len(route.legs)),
        "num_transfers": float(max(len(route.legs) - 1, 0)),
        "history_delay_mean": history_mean_delay,
        "history_delay_max": history_max_delay,
    }


FEATURE_ORDER = [
    "alerts_count",
    "vehicle_density",
    "time_of_day_minutes",
    "num_legs",
    "num_transfers",
    "history_delay_mean",
    "history_delay_max",
]


def feature_vector(features: dict[str, float]) -> list[float]:
    return [float(features.get(name, 0.0)) for name in FEATURE_ORDER]
