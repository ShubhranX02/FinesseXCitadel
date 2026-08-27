"""Create monthly point-in-time universe snapshots from a full base and official notices."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from finesse_portfolio.universe_reconstruction import (
    read_change_ledger,
    read_count_exceptions,
    reconstruct_month_end_universe,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-universe", default="data/universe_history_archive_only.csv")
    parser.add_argument("--changes", default="data/nse_index_change_ledger.csv")
    parser.add_argument("--count-exceptions", default="data/nse_index_count_exceptions.csv")
    parser.add_argument("--start", default="2022-04-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--validated-through", required=True)
    parser.add_argument("--output", default="data/universe_history.csv")
    parser.add_argument("--sources-output", default="data/universe_reconstruction_sources.csv")
    args = parser.parse_args()
    if pd.Timestamp(args.validated_through) < pd.Timestamp(args.end):
        raise SystemExit("--validated-through must be on or after --end; do not run an incomplete ledger.")

    base = pd.read_csv(args.base_universe, parse_dates=["effective_date"])
    changes = read_change_ledger(args.changes)
    count_exceptions = read_count_exceptions(args.count_exceptions)
    reconstructed = reconstruct_month_end_universe(base, changes, args.start, args.end, count_exceptions)
    first_reconstructed_date = pd.Timestamp(reconstructed["effective_date"].min())
    archive_history = base.loc[base["effective_date"] < first_reconstructed_date].copy()
    archive_history["derivation"] = "official_complete_archive"
    result = pd.concat([archive_history, reconstructed], ignore_index=True).sort_values(
        ["effective_date", "universe", "ticker"]
    )
    if result.duplicated(["effective_date", "ticker"]).any():
        raise RuntimeError("Combined archive and reconstruction history has duplicate ticker snapshots.")
    ledger_path = Path(args.changes)
    ledger_hash = hashlib.file_digest(ledger_path.open("rb"), "sha256").hexdigest()
    result.to_csv(args.output, index=False)
    sources = (
        changes[["effective_date", "universe", "source_url"]]
        .drop_duplicates()
        .assign(source_type="official_index_change_notice", ledger_sha256=ledger_hash)
        .sort_values(["effective_date", "universe", "source_url"])
    )
    sources.to_csv(args.sources_output, index=False)
    print(f"Wrote {len(result)} continuous membership rows to {args.output}")
    print(f"Wrote {len(sources)} official-notice provenance rows to {args.sources_output}")


if __name__ == "__main__":
    main()
