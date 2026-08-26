"""Download an official NSE monthly market-capitalisation archive by month."""
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from finesse_portfolio.nse_archive import market_cap_report_url, report_months


def main() -> None:
    parser = argparse.ArgumentParser(description="Download one official NSE monthly index report.")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--month", help="One report month as YYYY-MM")
    selection.add_argument("--start-month", help="First report month as YYYY-MM; requires --end-month")
    parser.add_argument("--end-month", help="Last report month as YYYY-MM; required with --start-month")
    parser.add_argument("--output-dir", default="data/raw/nse_market_cap_reports")
    args = parser.parse_args()
    if args.start_month and not args.end_month:
        parser.error("--end-month is required with --start-month")
    if args.end_month and not args.start_month:
        parser.error("--start-month is required with --end-month")
    months = [args.month] if args.month else report_months(args.start_month, args.end_month)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for month in months:
        url, filename = market_cap_report_url(month)
        destination = output / filename
        if destination.exists() and destination.stat().st_size >= 1_000:
            print(f"Keeping existing {destination}")
            continue
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as handle:
            handle.write(response.read())
        if destination.stat().st_size < 1_000:
            destination.unlink(missing_ok=True)
            raise RuntimeError(f"NSE returned an unexpectedly small file for {url}")
        print(f"Downloaded {destination} from {url}")


if __name__ == "__main__":
    main()
