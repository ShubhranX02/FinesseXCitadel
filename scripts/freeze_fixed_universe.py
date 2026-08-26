"""Create the organiser-approved fixed universe used by the production backtest."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

INDEXES = ("NIFTY_100", "NIFTY_MIDCAP_100", "NIFTY_SMALLCAP_100")


def _validate_snapshot(snapshot: pd.DataFrame, snapshot_date: pd.Timestamp) -> pd.DataFrame:
    required = {"effective_date", "ticker", "universe"}
    missing = required.difference(snapshot.columns)
    if missing:
        raise ValueError(f"Snapshot file is missing columns: {sorted(missing)}")
    selected = snapshot.loc[snapshot["effective_date"] == snapshot_date, list(required)].copy()
    counts = selected.groupby("universe")["ticker"].nunique().to_dict()
    expected = {index_name: 100 for index_name in INDEXES}
    if counts != expected:
        raise ValueError(f"Snapshot {snapshot_date.date()} is not a complete 300-stock universe: {counts}")
    if selected["ticker"].duplicated().any():
        raise ValueError("A ticker occurs in more than one fixed-universe index.")
    return selected.sort_values(["universe", "ticker"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze one official NSE snapshot for the whole backtest.")
    parser.add_argument("--input", default="data/universe_history_archive_only.csv")
    parser.add_argument("--source-manifest", default="data/universe_sources_archive_only.csv")
    parser.add_argument("--snapshot-date", default="2020-12-31")
    parser.add_argument("--start", default="2020-12-31")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--output", default="data/universe_fixed.csv")
    parser.add_argument("--sources-output", default="data/universe_fixed_sources.csv")
    args = parser.parse_args()

    snapshot_date = pd.Timestamp(args.snapshot_date)
    source = pd.read_csv(args.input, parse_dates=["effective_date"])
    snapshot = _validate_snapshot(source, snapshot_date)
    month_ends = pd.date_range(pd.Timestamp(args.start), pd.Timestamp(args.end), freq="ME")
    if month_ends.empty:
        raise ValueError("The requested fixed-universe period has no month ends.")

    fixed = pd.concat(
        [snapshot.assign(effective_date=month_end) for month_end in month_ends], ignore_index=True
    ).sort_values(["effective_date", "universe", "ticker"])
    fixed.to_csv(args.output, index=False)

    set_hash = hashlib.sha256(
        "\n".join(snapshot["ticker"].sort_values()).encode("utf-8")
    ).hexdigest()
    manifest_path = Path(args.source_manifest)
    if manifest_path.exists():
        sources = pd.read_csv(manifest_path)
        sources = sources.loc[sources["effective_date"].astype(str) == snapshot_date.date().isoformat()].copy()
    else:
        sources = pd.DataFrame({"universe": INDEXES, "source_url": "not recorded"})
    sources["fixed_snapshot_date"] = snapshot_date.date().isoformat()
    sources["fixed_set_sha256"] = set_hash
    sources["usage"] = "organiser-approved fixed universe for 2021-2025 backtest"
    sources.to_csv(args.sources_output, index=False)
    print(f"Wrote {len(fixed)} fixed-universe rows to {args.output}")
    print(f"Wrote provenance for {len(sources)} source snapshots to {args.sources_output}")


if __name__ == "__main__":
    main()
