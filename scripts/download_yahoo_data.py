"""Download adjusted prices for a supplied competition universe from Yahoo Finance."""
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
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()
    try:
        import yfinance as yf
    except ImportError as exc:
        raise SystemExit("Install the download extra: pip install -e '.[download]'") from exc

    tickers = sorted(load_universe(args.universe)["ticker"].unique())
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be positive")
    records: list[pd.DataFrame] = []
    failures: list[dict[str, str]] = []
    for start_index in range(0, len(tickers), args.batch_size):
        batch = tickers[start_index : start_index + args.batch_size]
        downloaded = yf.download(
            batch,
            start=args.start,
            end=args.end,
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=True,
        )
        for ticker in batch:
            try:
                frame = downloaded[ticker].dropna(how="all")
            except KeyError:
                frame = pd.DataFrame()
            if frame.empty:
                failures.append({"ticker": ticker, "reason": "no Yahoo Finance data returned"})
                continue
            frame.columns = [str(column).lower() for column in frame.columns]
            required = {"close", "volume"}
            if not required.issubset(frame.columns):
                failures.append({"ticker": ticker, "reason": "missing close or volume column"})
                continue
            clean = frame[["close", "volume"]].dropna(subset=["close"]).reset_index()
            clean = clean.rename(columns={"Date": "date", "date": "date"})
            clean["ticker"] = ticker
            records.append(clean[["date", "ticker", "close", "volume"]])
    if not records:
        raise SystemExit("No price records downloaded.")
    pd.concat(records, ignore_index=True).to_csv(output / "prices.csv", index=False)
    pd.DataFrame(failures, columns=["ticker", "reason"]).to_csv(
        output / "download_failures.csv", index=False
    )
    print(f"Downloaded prices for {len(records)} of {len(tickers)} tickers.")
    if failures:
        print(f"Recorded {len(failures)} unresolved Yahoo symbols in {output / 'download_failures.csv'}.")
    benchmark = yf.download(args.benchmark_ticker, start="2021-01-01", end=args.end, auto_adjust=True, progress=False)
    if benchmark.empty:
        raise SystemExit("No benchmark data returned; choose a valid Yahoo benchmark ticker.")
    benchmark.columns = [str(column[0] if isinstance(column, tuple) else column).lower() for column in benchmark.columns]
    benchmark[["close"]].reset_index().rename(columns={"Date": "date", "date": "date"}).to_csv(output / "benchmark.csv", index=False)


if __name__ == "__main__":
    main()
