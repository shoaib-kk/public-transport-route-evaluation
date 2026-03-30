from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from transport_app.config import APP_DATA_DIR, DB_PATH


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feed_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_type TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                snapshot_path TEXT NOT NULL,
                entity_count INTEGER NOT NULL DEFAULT 0,
                parsed_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS route_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT NOT NULL,
                route_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                request_json TEXT NOT NULL,
                response_json TEXT NOT NULL
            )
            """
        )


def record_feed_snapshot(
    *,
    feed_type: str,
    snapshot_path: Path,
    entity_count: int,
    parsed_count: int,
    status: str,
    details: dict[str, Any],
) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO feed_snapshots (
                feed_type, fetched_at, snapshot_path, entity_count, parsed_count, status, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feed_type,
                utc_now_iso(),
                str(snapshot_path),
                entity_count,
                parsed_count,
                status,
                json.dumps(details),
            ),
        )


def latest_feed_statuses() -> list[dict[str, Any]]:
    init_db()
    query = """
        SELECT fs.feed_type, fs.fetched_at, fs.snapshot_path, fs.entity_count, fs.parsed_count, fs.status, fs.details_json
        FROM feed_snapshots fs
        INNER JOIN (
            SELECT feed_type, MAX(id) AS max_id
            FROM feed_snapshots
            GROUP BY feed_type
        ) latest ON latest.max_id = fs.id
        ORDER BY fs.feed_type
    """
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
    return [
        {
            "feed_type": row["feed_type"],
            "fetched_at": row["fetched_at"],
            "snapshot_path": row["snapshot_path"],
            "entity_count": row["entity_count"],
            "parsed_count": row["parsed_count"],
            "status": row["status"],
            "details": json.loads(row["details_json"]),
        }
        for row in rows
    ]


def record_route_evaluation(
    *,
    route_id: str,
    route_name: str,
    request_payload: dict[str, Any],
    response_payload: dict[str, Any],
) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO route_evaluations (
                route_id, route_name, created_at, request_json, response_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                route_id,
                route_name,
                utc_now_iso(),
                json.dumps(request_payload),
                json.dumps(response_payload),
            ),
        )


def route_history(route_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """
    Return the most recent evaluations for a route (newest first).
    """
    init_db()
    query = """
        SELECT created_at, request_json, response_json
        FROM route_evaluations
        WHERE route_id = ?
        ORDER BY datetime(created_at) DESC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(query, (route_id, limit)).fetchall()

    history: list[dict[str, Any]] = []
    for row in rows:
        try:
            request_payload = json.loads(row["request_json"])
            response_payload = json.loads(row["response_json"])
        except json.JSONDecodeError:
            continue
        history.append(
            {
                "created_at": row["created_at"],
                "request": request_payload,
                "response": response_payload,
            }
        )
    return history
