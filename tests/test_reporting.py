import pandas as pd
import pytest

from finesse_portfolio.reporting import annual_returns, drawdown_series, trade_diagnostics


def test_annual_returns_chain_from_initial_capital() -> None:
    nav = pd.Series(
        [110.0, 121.0, 132.0],
        index=pd.to_datetime(["2021-12-31", "2022-01-03", "2022-12-30"]),
    )
    results = annual_returns(nav, initial_capital=100.0)
    assert results["net_return"].tolist() == pytest.approx([0.1, 0.2])


def test_drawdown_and_trade_diagnostics() -> None:
    nav = pd.Series([100.0, 120.0, 90.0], index=pd.date_range("2021-01-01", periods=3))
    assert round(drawdown_series(nav).iloc[-1], 2) == -0.25
    trades = pd.DataFrame(
        {
            "ticker": ["A.NS", "A.NS", "B.NS"],
            "side": ["BUY", "SELL", "BUY"],
            "gross_value": [100.0, 110.0, 200.0],
            "transaction_cost": [0.1, 0.11, 0.2],
        }
    )
    result = trade_diagnostics(trades, initial_capital=1000.0).set_index("ticker")
    assert result.loc["A.NS", "buy_trades"] == 1
    assert result.loc["A.NS", "sell_trades"] == 1
    assert result.loc["B.NS", "turnover_on_initial_capital"] == 0.2
