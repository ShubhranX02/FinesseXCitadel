from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_PRICE_COLUMNS = {"date", "ticker", "close"}
REQUIRED_UNIVERSE_COLUMNS = {"effective_date", "ticker", "universe"}


def load_prices(path: str | Path) -> pd.DataFrame:
    prices = pd.read_csv(path, parse_dates=["date"])
    missing = REQUIRED_PRICE_COLUMNS.difference(prices.columns)
    if missing:
        raise ValueError(f"Price data is missing columns: {sorted(missing)}")
    prices = prices.copy()
    prices["ticker"] = prices["ticker"].astype(str).str.upper().str.strip()
    prices = prices.sort_values(["date", "ticker"])
    if prices.duplicated(["date", "ticker"]).any():
        raise ValueError("Price data contains duplicate ticker-date records.")
    if (prices["close"] <= 0).any():
        raise ValueError("Price data contains non-positive close values.")
    return prices


def load_universe(path: str | Path) -> pd.DataFrame:
    universe = pd.read_csv(path, parse_dates=["effective_date"])
    missing = REQUIRED_UNIVERSE_COLUMNS.difference(universe.columns)
    if missing:
        raise ValueError(f"Universe data is missing columns: {sorted(missing)}")
    universe = universe.copy()
    universe["ticker"] = universe["ticker"].astype(str).str.upper().str.strip()
    if universe.duplicated(["effective_date", "ticker"]).any():
        raise ValueError("Universe data contains duplicate ticker-snapshot records.")
    allowed = {"NIFTY_100", "NIFTY_MIDCAP_100", "NIFTY_SMALLCAP_100"}
    bad = set(universe["universe"].dropna()).difference(allowed)
    if bad:
        raise ValueError(f"Unexpected universe labels: {sorted(bad)}")
    return universe.sort_values(["effective_date", "ticker"])


def load_benchmark(path: str | Path) -> pd.Series:
    benchmark = pd.read_csv(path, parse_dates=["date"])
    missing = {"date", "close"}.difference(benchmark.columns)
    if missing:
        raise ValueError(f"Benchmark data is missing columns: {sorted(missing)}")
    series = benchmark.set_index("date")["close"].sort_index().astype(float)
    if series.index.duplicated().any() or (series <= 0).any():
        raise ValueError("Benchmark contains duplicate dates or non-positive closes.")
    return series


def prices_to_wide(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pivot(index="date", columns="ticker", values="close").sort_index()
