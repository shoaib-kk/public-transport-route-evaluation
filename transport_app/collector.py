from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

from google.transit import gtfs_realtime_pb2

from transport_app.config import INGESTION_DIR
from transport_app.feed_processing import historical_feed_status
from transport_app.storage import record_feed_snapshot


if str(INGESTION_DIR) not in sys.path:
    sys.path.insert(0, str(INGESTION_DIR))

from download_static_gtfs import run as download_static_gtfs  # type: ignore  # noqa: E402
from pull_alerts import run as pull_alerts  # type: ignore  # noqa: E402
from pull_historical_gtfs import run as pull_historical_gtfs  # type: ignore  # noqa: E402
from pull_vehicle_positions import run as pull_vehicle_positions  # type: ignore  # noqa: E402


def _count_gtfs_entities(snapshot_path: Path) -> tuple[int, int]:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(snapshot_path.read_bytes())
    return len(feed.entity), len(feed.entity)


def _record_pb_snapshot(feed_type: str, snapshot_path: Path) -> Path:
    entity_count, parsed_count = _count_gtfs_entities(snapshot_path)
    record_feed_snapshot(
        feed_type=feed_type,
        snapshot_path=snapshot_path,
        entity_count=entity_count,
        parsed_count=parsed_count,
        status="ok",
        details={},
    )
    return snapshot_path


def _record_file_snapshot(feed_type: str, snapshot_path: Path, details: dict) -> Path:
    record_feed_snapshot(
        feed_type=feed_type,
        snapshot_path=snapshot_path,
        entity_count=0,
        parsed_count=0,
        status="ok",
        details=details,
    )
    return snapshot_path


def fetch_static() -> Path:
    path = Path(download_static_gtfs())
    return _record_file_snapshot("static", path, {"format": "zip"})


def fetch_alerts() -> Path:
    path = Path(pull_alerts())
    return _record_pb_snapshot("alerts", path)


def fetch_vehicle_positions() -> Path:
    path = Path(pull_vehicle_positions())
    return _record_pb_snapshot("vehicle_positions", path)


def fetch_historical(
    *,
    from_date: str,
    to_date: str,
    transport_mode: str = "MET",
    service_name: str = "Metro",
    schema_type: str = "VehiclePosition",
) -> Path:
    path = Path(
        pull_historical_gtfs(
            from_date=from_date,
            to_date=to_date,
            transport_mode=transport_mode,
            service_name=service_name,
            schema_type=schema_type,
        )
    )
    return _record_file_snapshot("historical", path, historical_feed_status())


def fetch_realtime_feeds() -> dict[str, Path]:
    return {
        "alerts": fetch_alerts(),
        "vehicle_positions": fetch_vehicle_positions(),
    }


def fetch_all(
    *,
    from_date: str | None = None,
    to_date: str | None = None,
    include_historical: bool = False,
) -> dict[str, Path]:
    results = {
        "static": fetch_static(),
        "alerts": fetch_alerts(),
        "vehicle_positions": fetch_vehicle_positions(),
    }
    if include_historical and from_date and to_date:
        results["historical"] = fetch_historical(from_date=from_date, to_date=to_date)
    return results
