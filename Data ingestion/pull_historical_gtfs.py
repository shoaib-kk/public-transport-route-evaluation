from __future__ import annotations

import argparse
import os
from pathlib import Path

from _download_utils import DATA_ROOT, api_headers, post_to_file


README_SOURCE_URL = "https://opendata.transport.nsw.gov.au/dataset/historical-gtfs-and-gtfs-realtime"
DEFAULT_HISTORICAL_GTFS_URL = os.getenv(
    "TFNSW_HISTORICAL_GTFS_URL",
    "https://api.transport.nsw.gov.au/v1/gtfs/historical",
)
DEFAULT_OUTPUT_DIR = DATA_ROOT / "historical"


def parse_args() -> argparse.Namespace:
    # parse command-line arguments to determine the historical GTFS API URL, parameters for the request, and output directory
    parser = argparse.ArgumentParser(
        description="Pull historical GTFS/GTFS-realtime archives into data/historical/."
    )
    parser.add_argument("--url", default=DEFAULT_HISTORICAL_GTFS_URL, help="Historical API URL.")
    parser.add_argument(
        "--transport-mode",
        default="MET",
        choices=["MET", "FER"],
        help="Transport mode expected by the historical GTFS API.",
    )
    parser.add_argument(
        "--service-name",
        default="Metro",
        choices=["Metro", "SydneyFerries"],
        help="Service name expected by the historical GTFS API.",
    )
    parser.add_argument(
        "--schema-type",
        default="VehiclePosition",
        choices=["TripUpdate", "VehiclePosition", "Timetable"],
        help="Historical feed type to request.",
    )
    parser.add_argument(
        "--from-date",
        required=True,
        help="Start date in YYYY-MM-DD format. The API allows a maximum 90-day range.",
    )
    parser.add_argument(
        "--to-date",
        required=True,
        help="End date in YYYY-MM-DD format. The API allows a maximum 90-day range.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Folder to save the downloaded file into.",
    )
    return parser.parse_args()


def run(
    *,
    url: str = DEFAULT_HISTORICAL_GTFS_URL,
    transport_mode: str = "MET",
    service_name: str = "Metro",
    schema_type: str = "VehiclePosition",
    from_date: str,
    to_date: str,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    # Send a POST request to the historical GTFS API with the specified parameters and save the response content to a file in the output directory
    payload = {
        "transportMode": transport_mode,
        "serviceName": service_name,
        "schemaType": schema_type,
        "fromDate": from_date,
        "toDate": to_date,
    }
    headers = dict(api_headers())
    headers["Accept"] = "application/octet-stream"
    headers["Content-Type"] = "application/json"

    output_path = post_to_file(
        url=url,
        destination_dir=Path(output_dir),
        filename_stem="historical_gtfs",
        headers=headers,
        json_body=payload,
        fallback_extension=".zip",
    )
    return output_path


def main() -> None:
    args = parse_args()
    output_path = run(
        url=args.url,
        transport_mode=args.transport_mode,
        service_name=args.service_name,
        schema_type=args.schema_type,
        from_date=args.from_date,
        to_date=args.to_date,
        output_dir=args.output_dir,
    )
    print(f"README source: {README_SOURCE_URL}")
    print(f"Saved historical GTFS to {output_path}")


if __name__ == "__main__":
    main()
