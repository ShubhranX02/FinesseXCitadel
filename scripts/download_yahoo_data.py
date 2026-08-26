"""Download adjusted prices for a supplied, point-in-time membership file."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from finesse_portfolio.data import load_universe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, help="Point-in-time membership CSV")
    parser.add_argument("--benchmark-ticker", default="^CRSLDX", help="Yahoo Finance benchmark symbol")
    parser.add_argument("--start", default="2019-11-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--output-dir", default="data/raw")
    args = parser.parse_args()
    try:
        import yfinance as yf
    except ImportError as exc:
        raise SystemExit("Install the download extra: pip install -e '.[download]'") from exc

    tickers = sorted(load_universe(args.universe)["ticker"].unique())
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records: list[pd.DataFrame] = []
    for ticker in tickers:
        frame = yf.download(ticker, start=args.start, end=args.end, auto_adjust=True, progress=False)
        if frame.empty:
            print(f"WARNING: no data returned for {ticker}")
            continue
        frame.columns = [str(column[0] if isinstance(column, tuple) else column).lower() for column in frame.columns]
        required = {"close", "volume"}
        if not required.issubset(frame.columns):
            print(f"WARNING: malformed data returned for {ticker}")
            continue
        clean = frame[["close", "volume"]].reset_index().rename(columns={"Date": "date", "date": "date"})
        clean["ticker"] = ticker
        records.append(clean[["date", "ticker", "close", "volume"]])
    if not records:
        raise SystemExit("No price records downloaded.")
    pd.concat(records, ignore_index=True).to_csv(output / "prices.csv", index=False)
    benchmark = yf.download(args.benchmark_ticker, start="2021-01-01", end=args.end, auto_adjust=True, progress=False)
    if benchmark.empty:
        raise SystemExit("No benchmark data returned; choose a valid Yahoo benchmark ticker.")
    benchmark.columns = [str(column[0] if isinstance(column, tuple) else column).lower() for column in benchmark.columns]
    benchmark[["close"]].reset_index().rename(columns={"Date": "date", "date": "date"}).to_csv(output / "benchmark.csv", index=False)


if __name__ == "__main__":
    main()
