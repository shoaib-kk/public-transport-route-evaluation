from __future__ import annotations

import argparse
import time
from datetime import date, timedelta

from transport_app.collector import fetch_all, fetch_realtime_feeds
from transport_app.config import DEFAULT_POLL_INTERVAL_SECONDS
from transport_app.storage import init_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Polling loop for TfNSW feeds. Realtime feeds refresh every interval; static can be fetched once on startup."
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Polling interval for realtime feeds.",
    )
    parser.add_argument(
        "--with-static",
        action="store_true",
        help="Fetch static GTFS once before entering the realtime loop.",
    )
    parser.add_argument(
        "--with-historical",
        action="store_true",
        help="Fetch one historical snapshot before entering the realtime loop.",
    )
    parser.add_argument(
        "--from-date",
        default=(date.today() - timedelta(days=7)).isoformat(),
        help="Historical start date if --with-historical is enabled.",
    )
    parser.add_argument(
        "--to-date",
        default=date.today().isoformat(),
        help="Historical end date if --with-historical is enabled.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    init_db()

    if args.with_static or args.with_historical:
        fetch_all(
            from_date=args.from_date,
            to_date=args.to_date,
            include_historical=args.with_historical,
        )

    while True:
        results = fetch_realtime_feeds()
        print(f"Fetched realtime feeds: {results}")
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
