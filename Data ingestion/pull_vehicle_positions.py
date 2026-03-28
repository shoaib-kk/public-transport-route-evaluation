from __future__ import annotations

import argparse
import os
from pathlib import Path

from _download_utils import DATA_ROOT, api_headers, download_to_file


README_SOURCE_URL = (
    "https://opendata.transport.nsw.gov.au/data/dataset/public-transport-realtime-vehicle-positions-v2"
)
DEFAULT_VEHICLE_POSITIONS_URL = os.getenv(
    "TFNSW_VEHICLE_POSITIONS_URL",
    "https://api.transport.nsw.gov.au/v2/gtfs/vehiclepos/sydneytrains",
)
DEFAULT_OUTPUT_DIR = DATA_ROOT / "realtime" / "vehicle_positions"


def parse_args() -> argparse.Namespace:
    # parse command-line arguments to determine the vehicle positions feed URL and output directory
    parser = argparse.ArgumentParser(
        description="Pull realtime GTFS vehicle positions into data/realtime/vehicle_positions/."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_VEHICLE_POSITIONS_URL,
        help="Vehicle positions feed URL.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Folder to save the downloaded file into.",
    )
    return parser.parse_args()


def run(
    *,
    url: str = DEFAULT_VEHICLE_POSITIONS_URL,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    # Download the vehicle positions feed from the specified URL and save it to the output directory
    # basically just a wrapper around download_to_file with the right parameters for the vehicle positions feed
    output_path = download_to_file(
        url=url,
        destination_dir=Path(output_dir),
        filename_stem="vehicle_positions",
        headers=api_headers(),
        fallback_extension=".pb",
    )
    return output_path


def main() -> None:
    args = parse_args()
    output_path = run(url=args.url, output_dir=args.output_dir)
    print(f"README source: {README_SOURCE_URL}")
    print(f"Saved vehicle positions feed to {output_path}")


if __name__ == "__main__":
    main()
