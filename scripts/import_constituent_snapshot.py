"""Turn three NSE constituent downloads into one validated point-in-time snapshot."""
from __future__ import annotations

import argparse
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
    print(f"Saved {len(snapshot)} constituents for {args.effective_date} to {output}")


if __name__ == "__main__":
    main()
