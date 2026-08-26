"""Extract a complete Nifty 100/Midcap 100/Smallcap 100 snapshot from one NSE archive."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from finesse_portfolio.nse_constituents import snapshot_from_archive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--effective-date", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--output", default="data/universe_history.csv")
    parser.add_argument("--sources-output", default="data/universe_sources.csv")
    args = parser.parse_args()

    archive = Path(args.archive)
    snapshot = snapshot_from_archive(archive, args.effective_date)
    output = Path(args.output)
    existing = pd.read_csv(output) if output.exists() else pd.DataFrame(columns=snapshot.columns)
    existing = existing[existing["effective_date"].astype(str) != args.effective_date]
    pd.concat([existing, snapshot], ignore_index=True).sort_values(["effective_date", "ticker"]).to_csv(
        output, index=False
    )
    sources_output = Path(args.sources_output)
    source_records = pd.DataFrame(
        [
            {
                "effective_date": args.effective_date,
                "universe": universe,
                "source_url": args.source_url,
                "local_filename": archive.name,
                "sha256": hashlib.file_digest(archive.open("rb"), "sha256").hexdigest(),
                "constituent_count": 100,
            }
            for universe in snapshot["universe"].unique()
        ]
    )
    existing_sources = pd.read_csv(sources_output) if sources_output.exists() else pd.DataFrame(columns=source_records.columns)
    existing_sources = existing_sources[existing_sources["effective_date"].astype(str) != args.effective_date]
    pd.concat([existing_sources, source_records], ignore_index=True).sort_values(
        ["effective_date", "universe"]
    ).to_csv(sources_output, index=False)
    print(f"Extracted {len(snapshot)} constituents from {archive.name}")


if __name__ == "__main__":
    main()
