import pandas as pd
import pytest

from finesse_portfolio.backtest import run_backtest
from finesse_portfolio.config import StrategyConfig


def test_initial_purchase_charges_transaction_cost() -> None:
    dates = pd.bdate_range("2020-01-01", "2021-02-05")
    prices = pd.DataFrame({"A.NS": 100.0}, index=dates)
    universe = pd.DataFrame({"effective_date": [pd.Timestamp("2020-12-31")], "ticker": ["A.NS"], "universe": ["NIFTY_100"]})
    config = StrategyConfig(
        strategy_name="test", start_date="2021-01-01", end_date="2021-02-05", initial_capital=1000.0,
        transaction_cost_rate=0.001, holdings=1, max_weight=1.0, min_price_history_days=252,
        momentum_long_days=252, momentum_skip_days=21, momentum_short_days=126, volatility_days=63,
        signal_weights={"momentum_12_1": 1.0, "momentum_6": 0.0, "low_volatility": 0.0},
        benchmark_name="TEST", prices_path="", universe_path="", benchmark_path="", output_dir="",
    )
    result = run_backtest(prices, universe, config)
    assert round(result.nav.iloc[-1], 6) == 999.000999
    assert len(result.trades) == 1
    assert result.trades.iloc[0]["side"] == "BUY"
    assert result.trades.iloc[0]["date"] == pd.Timestamp("2021-01-01")


def test_backtest_rejects_missing_universe_coverage() -> None:
    dates = pd.bdate_range("2020-01-01", "2021-02-05")
    prices = pd.DataFrame({"A.NS": 100.0}, index=dates)
    universe = pd.DataFrame(
        {
            "effective_date": [pd.Timestamp("2021-01-31")],
            "ticker": ["A.NS"],
            "universe": ["NIFTY_100"],
        }
    )
    config = StrategyConfig(
        strategy_name="test", start_date="2021-01-01", end_date="2021-02-05", initial_capital=1000.0,
        transaction_cost_rate=0.001, holdings=1, max_weight=1.0, min_price_history_days=252,
        momentum_long_days=252, momentum_skip_days=21, momentum_short_days=126, volatility_days=63,
        signal_weights={"momentum_12_1": 1.0, "momentum_6": 0.0, "low_volatility": 0.0},
        benchmark_name="TEST", prices_path="", universe_path="", benchmark_path="", output_dir="",
    )
    with pytest.raises(ValueError, match="No point-in-time universe snapshot"):
        run_backtest(prices, universe, config)
