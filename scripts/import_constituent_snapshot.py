"""Turn three NSE constituent downloads into one validated point-in-time snapshot."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from finesse_portfolio.universe import read_constituents

INPUTS = {
    "nifty_100": "NIFTY_100",
    "midcap_100": "NIFTY_MIDCAP_100",
    "smallcap_100": "NIFTY_SMALLCAP_100",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import one complete historical index snapshot.")
    parser.add_argument("--effective-date", required=True, help="YYYY-MM-DD; use the date the snapshot became tradable")
    parser.add_argument("--nifty-100", required=True)
    parser.add_argument("--midcap-100", required=True)
    parser.add_argument("--smallcap-100", required=True)
    parser.add_argument("--output", default="data/universe_history.csv")
    parser.add_argument("--sources-output", default="data/universe_sources.csv")
    parser.add_argument("--nifty-100-source", required=True, help="Official source URL or archive URL")
    parser.add_argument("--midcap-100-source", required=True, help="Official source URL or archive URL")
    parser.add_argument("--smallcap-100-source", required=True, help="Official source URL or archive URL")
    args = parser.parse_args()

    snapshot = pd.concat(
        [
            read_constituents(getattr(args, argument), label, args.effective_date)
            for argument, label in INPUTS.items()
        ],
        ignore_index=True,
    )
    if snapshot["ticker"].duplicated().any():
        raise ValueError("A ticker appears in more than one index snapshot.")
    output = Path(args.output)
    existing = pd.read_csv(output) if output.exists() else pd.DataFrame(columns=snapshot.columns)
    existing = existing[existing["effective_date"].astype(str) != args.effective_date]
    combined = pd.concat([existing, snapshot], ignore_index=True).sort_values(["effective_date", "ticker"])
    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output, index=False)
    source_rows = []
    source_arguments = {
        "nifty_100": "nifty_100_source",
        "midcap_100": "midcap_100_source",
        "smallcap_100": "smallcap_100_source",
    }
    for argument, label in INPUTS.items():
        file_path = Path(getattr(args, argument))
        source_rows.append(
            {
                "effective_date": args.effective_date,
                "universe": label,
                "source_url": getattr(args, source_arguments[argument]),
                "local_filename": file_path.name,
                "sha256": hashlib.file_digest(file_path.open("rb"), "sha256").hexdigest(),
                "constituent_count": 100,
            }
        )
    sources_output = Path(args.sources_output)
    existing_sources = (
        pd.read_csv(sources_output) if sources_output.exists() else pd.DataFrame(columns=source_rows[0].keys())
    )
    existing_sources = existing_sources[
        existing_sources["effective_date"].astype(str) != args.effective_date
    ]
    pd.concat([existing_sources, pd.DataFrame(source_rows)], ignore_index=True).sort_values(
        ["effective_date", "universe"]
    ).to_csv(sources_output, index=False)
    print(f"Saved {len(snapshot)} constituents for {args.effective_date} to {output}")


if __name__ == "__main__":
    main()
