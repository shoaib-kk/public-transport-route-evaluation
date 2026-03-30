from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from google.transit import gtfs_realtime_pb2

from transport_app.config import ALERTS_DIR, HISTORICAL_DIR, STATIC_DIR, VEHICLE_POSITIONS_DIR


@dataclass
class AlertsSummary:
    entity_count: int = 0
    route_alert_counts: dict[str, int] = field(default_factory=dict)
    headers_by_route: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class VehiclePositionsSummary:
    entity_count: int = 0
    route_vehicle_counts: dict[str, int] = field(default_factory=dict)
    latest_vehicle_timestamp: int | None = None


def latest_file(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def parse_alerts(path: Path | None = None) -> AlertsSummary:
    """Parse the latest alerts feed snapshot and return a summary of the alerts
    particularly counts by route and unique headers."""
    snapshot = path or latest_file(ALERTS_DIR, "*.pb")
    summary = AlertsSummary()
    if snapshot is None:
        return summary

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(snapshot.read_bytes())
    summary.entity_count = len(feed.entity)

    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue
        alert = entity.alert
        header = ""
        if alert.header_text.translation:
            header = alert.header_text.translation[0].text
        for informed in alert.informed_entity:
            route_id = informed.route_id or "UNKNOWN"
            summary.route_alert_counts[route_id] = summary.route_alert_counts.get(route_id, 0) + 1
            summary.headers_by_route.setdefault(route_id, [])
            if header and header not in summary.headers_by_route[route_id]:
                summary.headers_by_route[route_id].append(header)
    return summary


def parse_vehicle_positions(path: Path | None = None) -> VehiclePositionsSummary:
    """Parse the latest vehicle positions feed snapshot and return a summary of the vehicle positions"""
    snapshot = path or latest_file(VEHICLE_POSITIONS_DIR, "*.pb")
    summary = VehiclePositionsSummary()
    if snapshot is None:
        return summary

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(snapshot.read_bytes())
    summary.entity_count = len(feed.entity)

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        vehicle = entity.vehicle
        route_id = vehicle.trip.route_id or "UNKNOWN"
        summary.route_vehicle_counts[route_id] = summary.route_vehicle_counts.get(route_id, 0) + 1
        if vehicle.timestamp:
            ts = int(vehicle.timestamp)
            if summary.latest_vehicle_timestamp is None or ts > summary.latest_vehicle_timestamp:
                summary.latest_vehicle_timestamp = ts
    return summary


def static_feed_status() -> dict[str, str | int | None]:
    """Check for the latest static feed snapshot and return path and availability status"""
    snapshot = latest_file(STATIC_DIR, "*.zip")
    return {
        "snapshot_path": str(snapshot) if snapshot else None,
        "available": snapshot is not None,
    }


def historical_feed_status() -> dict[str, str | int | None]:
    """Check for the latest historical feed snapshot and return path and availability status"""
    snapshot = latest_file(HISTORICAL_DIR, "*.json")
    details: dict[str, str | int | None] = {
        "snapshot_path": str(snapshot) if snapshot else None,
        "available": snapshot is not None,
    }
    if snapshot is None:
        return details
    try:
        payload = json.loads(snapshot.read_text(encoding="utf-8"))
        details["file_count"] = len(payload.get("files", []))
        details["requestdetails"] = payload.get("requestdetails")
    except json.JSONDecodeError:
        details["file_count"] = None
    return details


def vehicle_feed_age_seconds(summary: VehiclePositionsSummary) -> int | None:
    if summary.latest_vehicle_timestamp is None:
        return None
    current = datetime.now(timezone.utc).timestamp()
    return max(0, int(current - summary.latest_vehicle_timestamp))
