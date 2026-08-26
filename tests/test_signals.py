import pandas as pd

from finesse_portfolio.config import StrategyConfig
from finesse_portfolio.signals import eligible_tickers, factor_scores, rebalance_dates


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


def test_quarterly_rebalance_dates_use_calendar_quarter_ends() -> None:
    dates = pd.bdate_range("2020-12-01", "2021-12-31")
    result = rebalance_dates(dates, pd.Timestamp("2020-12-01"), pd.Timestamp("2021-12-31"), "quarterly")
    assert [date.month for date in result] == [12, 3, 6, 9, 12]


def test_quality_score_rewards_roe_and_penalises_debt() -> None:
    dates = pd.bdate_range("2020-01-01", "2021-01-29")
    prices = pd.DataFrame({"A.NS": range(100, 100 + len(dates)), "B.NS": range(100, 100 + len(dates))}, index=dates)
    universe = pd.DataFrame(
        {"effective_date": [pd.Timestamp("2020-12-31")] * 2, "ticker": ["A.NS", "B.NS"], "universe": ["NIFTY_100"] * 2}
    )
    fundamentals = pd.DataFrame(
        {"reported_date": [pd.Timestamp("2020-12-01")] * 2, "ticker": ["A.NS", "B.NS"], "roe": [25.0, 10.0], "debt_to_equity": [0.2, 2.0]}
    )
    config = StrategyConfig(
        strategy_name="quality", start_date="2021-01-01", end_date="2021-01-31", initial_capital=1.0,
        transaction_cost_rate=0.001, holdings=1, max_weight=1.0, min_price_history_days=252,
        momentum_long_days=252, momentum_skip_days=21, momentum_short_days=126, volatility_days=63,
        signal_weights={"quality_roe_debt": 1.0}, benchmark_name="TEST", prices_path="", universe_path="",
        benchmark_path="", output_dir="", rebalance_frequency="quarterly",
    )
    scores = factor_scores(prices, pd.Timestamp("2021-01-29"), universe, config, fundamentals)
    assert scores.index[0] == "A.NS"
