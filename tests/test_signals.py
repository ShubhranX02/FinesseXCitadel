import pandas as pd

from finesse_portfolio.signals import eligible_tickers


def test_universe_uses_latest_known_snapshot() -> None:
    universe = pd.DataFrame(
        {
            "effective_date": pd.to_datetime(["2020-01-01", "2021-01-01"]),
            "ticker": ["A.NS", "B.NS"],
            "universe": ["NIFTY_100", "NIFTY_100"],
        }
    )
    assert eligible_tickers(universe, pd.Timestamp("2020-12-31")) == {"A.NS"}
    assert eligible_tickers(universe, pd.Timestamp("2021-01-31")) == {"B.NS"}
