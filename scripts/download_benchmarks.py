#!/usr/bin/env python3
"""Download named Yahoo Finance benchmark series without replacing stock prices."""

from __future__ import annotations

from pathlib import Path

import yfinance as yf

BENCHMARKS = {"nifty50": "^NSEI", "nifty100": "^CNX100"}


def main() -> None:
    output = Path("data/raw")
    output.mkdir(parents=True, exist_ok=True)
    for name, ticker in BENCHMARKS.items():
        prices = yf.download(
            ticker,
            start="2021-01-01",
            end="2026-01-01",
            auto_adjust=True,
            progress=False,
        )
        if prices.empty:
            raise RuntimeError(f"No price data returned for {ticker}")
        prices.columns = [str(column[0] if isinstance(column, tuple) else column).lower() for column in prices.columns]
        prices[["close"]].reset_index().rename(columns={"Date": "date", "date": "date"}).to_csv(
            output / f"benchmark_{name}.csv", index=False
        )


if __name__ == "__main__":
    main()
