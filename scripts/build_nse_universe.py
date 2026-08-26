"""Extract all downloaded official NSE monthly archives into a validated point-in-time universe."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from finesse_portfolio.nse_archive import market_cap_report_url
from finesse_portfolio.nse_constituents import archive_coverage, snapshot_from_archive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archives-dir", default="data/raw/nse_market_cap_reports")
    parser.add_argument("--output", default="data/universe_history.csv")
    parser.add_argument("--sources-output", default="data/universe_sources.csv")
    parser.add_argument("--coverage-output", default="data/nse_archive_coverage.csv")
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help=(
            "Write only complete archive snapshots. Use a non-production output path: "
            "this does not create a full 2021-25 universe."
        ),
    )
    args = parser.parse_args()
    archives = sorted(Path(args.archives_dir).glob("indices_data*.zip"))
    if not archives:
        raise SystemExit("No NSE archive ZIPs found.")
    snapshots, sources, coverage = [], [], []
    for archive in archives:
        status = archive_coverage(archive)
        coverage.append(status)
        if not status["complete"]:
            print(
                f"Incomplete {archive.name}: missing or ambiguous "
                f"{status['missing_universes'] or 'required PDFs'}"
            )
            continue
        snapshot = snapshot_from_archive(archive)
        effective_date = snapshot["effective_date"].iloc[0]
        report_month = pd.Timestamp(effective_date).strftime("%Y-%m")
        source_url, _ = market_cap_report_url(report_month)
        digest = hashlib.file_digest(archive.open("rb"), "sha256").hexdigest()
        snapshots.append(snapshot)
        sources.extend(
            {
                "effective_date": effective_date,
                "universe": universe,
                "source_url": source_url,
                "local_filename": archive.name,
                "sha256": digest,
                "constituent_count": 100,
            }
            for universe in snapshot["universe"].unique()
        )
        print(f"Validated {archive.name}: {effective_date}, 300 constituents")
    coverage_frame = pd.DataFrame(coverage)
    coverage_frame.to_csv(args.coverage_output, index=False)
    incomplete_count = int((~coverage_frame["complete"]).sum())
    if incomplete_count and not args.allow_incomplete:
        raise SystemExit(
            f"{incomplete_count} of {len(coverage_frame)} archives are incomplete. "
            f"Coverage report written to {args.coverage_output}. No universe files were changed. "
            "Use official index-change notices to bridge the gap; do not silently carry "
            "forward an old constituent list."
        )
    if not snapshots:
        raise SystemExit("No complete archives found; no universe files were written.")
    pd.concat(snapshots, ignore_index=True).sort_values(["effective_date", "ticker"]).to_csv(args.output, index=False)
    pd.DataFrame(sources).sort_values(["effective_date", "universe"]).to_csv(args.sources_output, index=False)


if __name__ == "__main__":
    main()
