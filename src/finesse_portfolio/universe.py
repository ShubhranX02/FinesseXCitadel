from __future__ import annotations

import pandas as pd


def read_constituents(path: str, universe: str, effective_date: str) -> pd.DataFrame:
    """Read one official Nifty constituent CSV and normalise symbols for Yahoo prices."""
    source = pd.read_csv(path)
    symbol_column = next((column for column in source.columns if column.strip().lower() == "symbol"), None)
    if symbol_column is None:
        raise ValueError(f"{path} must contain an NSE 'Symbol' column.")
    symbols = source[symbol_column].dropna().astype(str).str.upper().str.strip()
    if len(symbols) != 100 or symbols.duplicated().any():
        raise ValueError(f"{path} must contain exactly 100 unique constituents.")
    return pd.DataFrame(
        {"effective_date": effective_date, "ticker": symbols + ".NS", "universe": universe}
    )
