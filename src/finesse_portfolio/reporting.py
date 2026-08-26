from __future__ import annotations

import pandas as pd


def drawdown_series(nav: pd.Series) -> pd.Series:
    """Return the peak-to-trough loss on each valuation date."""
    return (nav / nav.cummax() - 1).rename("drawdown")


def annual_returns(nav: pd.Series, initial_capital: float) -> pd.DataFrame:
    """Calculate calendar-year net returns from the same NAV series used for scoring."""
    records: list[dict[str, float | int]] = []
    prior_end = initial_capital
    for year, values in nav.groupby(nav.index.year):
        ending_value = float(values.iloc[-1])
        records.append(
            {
                "year": int(year),
                "opening_value": prior_end,
                "closing_value": ending_value,
                "net_return": ending_value / prior_end - 1,
            }
        )
        prior_end = ending_value
    return pd.DataFrame(records)


def trade_diagnostics(trades: pd.DataFrame, initial_capital: float) -> pd.DataFrame:
    """Produce auditable stock-level trade and cost statistics for the submission report."""
    columns = [
        "ticker",
        "total_trades",
        "buy_trades",
        "sell_trades",
        "gross_bought",
        "gross_sold",
        "gross_traded",
        "transaction_cost",
        "turnover_on_initial_capital",
    ]
    if trades.empty:
        return pd.DataFrame(columns=columns)
    diagnostics = trades.groupby("ticker", as_index=False).agg(
        total_trades=("side", "size"),
        buy_trades=("side", lambda side: int((side == "BUY").sum())),
        sell_trades=("side", lambda side: int((side == "SELL").sum())),
        gross_bought=("gross_value", lambda values: float(values[trades.loc[values.index, "side"] == "BUY"].sum())),
        gross_sold=("gross_value", lambda values: float(values[trades.loc[values.index, "side"] == "SELL"].sum())),
        gross_traded=("gross_value", "sum"),
        transaction_cost=("transaction_cost", "sum"),
    )
    diagnostics["turnover_on_initial_capital"] = diagnostics["gross_traded"] / initial_capital
    return diagnostics[columns].sort_values("gross_traded", ascending=False)
