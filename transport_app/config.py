from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATIC_DIR = DATA_DIR / "static"
ALERTS_DIR = DATA_DIR / "realtime" / "alerts"
VEHICLE_POSITIONS_DIR = DATA_DIR / "realtime" / "vehicle_positions"
HISTORICAL_DIR = DATA_DIR / "historical"
APP_DATA_DIR = PROJECT_ROOT / "app_data"
DB_PATH = APP_DATA_DIR / "transport_app.db"
MODELS_DIR = APP_DATA_DIR / "models"
METRICS_DIR = APP_DATA_DIR / "metrics"
LOG_DIR = APP_DATA_DIR / "logs"

INGESTION_DIR = PROJECT_ROOT / "Data ingestion"
DEFAULT_POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
