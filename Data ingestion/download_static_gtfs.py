from __future__ import annotations

import argparse
import os
from pathlib import Path

from _download_utils import DATA_ROOT, api_headers, download_to_file


README_SOURCE_URL = "https://opendata.transport.nsw.gov.au/dataset/timetables-complete-gtfs"
DEFAULT_STATIC_GTFS_URL = os.getenv(
    "TFNSW_STATIC_GTFS_URL",
    "https://api.transport.nsw.gov.au/v1/gtfs/schedule/sydneytrains",
)
DEFAULT_OUTPUT_DIR = DATA_ROOT / "static"


def parse_args() -> argparse.Namespace:
    # parse command-line arguments to determine the GTFS source URL and output directory
    parser = argparse.ArgumentParser(
        description="Download the static GTFS bundle into data/static/."
    )
    parser.add_argument("--url", default=DEFAULT_STATIC_GTFS_URL, help="GTFS source URL.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Folder to save the downloaded file into.",
    )
    return parser.parse_args()


def run(*, url: str = DEFAULT_STATIC_GTFS_URL, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> Path:
    # Download the static GTFS data from the specified URL and save it to the output directory
    # basically just a wrapper around download_to_file with the right parameters for static GTFS
    output_path = download_to_file(
        url=url,
        destination_dir=Path(output_dir),
        filename_stem="static_gtfs",
        headers=api_headers(),
        fallback_extension=".zip",
    )
    return output_path


def main() -> None:
    args = parse_args()
    output_path = run(url=args.url, output_dir=args.output_dir)
    print(f"README source: {README_SOURCE_URL}")
    print(f"Saved static GTFS to {output_path}")


if __name__ == "__main__":
    main()
