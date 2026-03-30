from __future__ import annotations

from statistics import mean
from typing import Any

from transport_app.storage import route_history


def rolling_summary(route_id: str, limit: int = 100) -> dict[str, Any]:
    """
    Compute rolling aggregates for a route based on stored evaluations.
    """
    history = route_history(route_id, limit=limit)
    if not history:
        return {"count": 0, "delay_mean": 0.0, "delay_p95": 0.0, "reliability_mean": 0.0}

    delays = [
        entry["response"].get("expected_delay_minutes", 0)
        for entry in history
        if isinstance(entry.get("response"), dict)
    ]
    reliabilities = [
        entry["response"].get("route_reliability_score", 0)
        for entry in history
        if isinstance(entry.get("response"), dict)
    ]
    delays_sorted = sorted(delays)
    p95_idx = max(int(len(delays_sorted) * 0.95) - 1, 0)
    return {
        "count": len(history),
        "delay_mean": float(mean(delays)) if delays else 0.0,
        "delay_p95": float(delays_sorted[p95_idx]) if delays else 0.0,
        "reliability_mean": float(mean(reliabilities)) if reliabilities else 0.0,
    }


def route_timeseries(route_id: str, limit: int = 200) -> list[dict[str, Any]]:
    """
    Chronological series (oldest first) for plotting trends.
    """
    history = route_history(route_id, limit=limit)
    history.reverse()
    return [
        {
            "created_at": entry["created_at"],
            "expected_delay_minutes": entry["response"].get("expected_delay_minutes", 0),
            "route_reliability_score": entry["response"].get("route_reliability_score", 0),
        }
        for entry in history
        if isinstance(entry.get("response"), dict)
    ]
