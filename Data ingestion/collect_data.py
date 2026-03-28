from __future__ import annotations

import argparse
from datetime import date, timedelta

from download_static_gtfs import run as download_static_gtfs
from pull_alerts import run as pull_alerts
from pull_historical_gtfs import run as pull_historical_gtfs
from pull_vehicle_positions import run as pull_vehicle_positions


def default_from_date(days_back: int) -> str:
    return (date.today() - timedelta(days=days_back)).isoformat()


def default_to_date() -> str:
    return date.today().isoformat()


def parse_args() -> argparse.Namespace:
    # parse command-line arguments to determine which data to download and the parameters for historical data
    parser = argparse.ArgumentParser(
        description="Temporary pipeline to download static, realtime, and historical TfNSW data."
    )
    parser.add_argument(
        "--skip-static",
        action="store_true",
        help="Skip the static GTFS download.",
    )
    parser.add_argument(
        "--skip-alerts",
        action="store_true",
        help="Skip the realtime alerts download.",
    )
    parser.add_argument(
        "--skip-vehicle-positions",
        action="store_true",
        help="Skip the realtime vehicle positions download.",
    )
    parser.add_argument(
        "--skip-historical",
        action="store_true",
        help="Skip the historical GTFS download.",
    )
    parser.add_argument(
        "--from-date",
        default=default_from_date(7),
        help="Historical start date in YYYY-MM-DD format. Defaults to 7 days ago.",
    )
    parser.add_argument(
        "--to-date",
        default=default_to_date(),
        help="Historical end date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--transport-mode",
        default="MET",
        choices=["MET", "FER"],
        help="Historical API transport mode.",
    )
    parser.add_argument(
        "--service-name",
        default="Metro",
        choices=["Metro", "SydneyFerries"],
        help="Historical API service name.",
    )
    parser.add_argument(
        "--schema-type",
        default="VehiclePosition",
        choices=["TripUpdate", "VehiclePosition", "Timetable"],
        help="Historical API schema type.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.skip_static:
        output_path = download_static_gtfs()
        print(f"Saved static GTFS to {output_path}")

    if not args.skip_alerts:
        output_path = pull_alerts()
        print(f"Saved alerts feed to {output_path}")

    if not args.skip_vehicle_positions:
        output_path = pull_vehicle_positions()
        print(f"Saved vehicle positions feed to {output_path}")

    if not args.skip_historical:
        output_path = pull_historical_gtfs(
            from_date=args.from_date,
            to_date=args.to_date,
            transport_mode=args.transport_mode,
            service_name=args.service_name,
            schema_type=args.schema_type,
        )
        print(f"Saved historical GTFS to {output_path}")


if __name__ == "__main__":
    main()
