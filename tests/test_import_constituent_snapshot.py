import pandas as pd
import pytest

from finesse_portfolio.universe import read_constituents


def test_snapshot_requires_exactly_100_unique_symbols(tmp_path) -> None:
    source = tmp_path / "constituents.csv"
    pd.DataFrame({"Symbol": ["ABC", "ABC"]}).to_csv(source, index=False)
    with pytest.raises(ValueError, match="exactly 100 unique"):
        read_constituents(str(source), "NIFTY_100", "2021-01-01")
