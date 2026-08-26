from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import StrategyConfig
from .signals import factor_scores, monthly_decision_dates, target_weights


@dataclass
class BacktestResult:
    nav: pd.Series
    holdings: pd.DataFrame
    trades: pd.DataFrame
    realised_sales: pd.DataFrame
    targets: pd.DataFrame


def _next_trading_date(index: pd.DatetimeIndex, date: pd.Timestamp) -> pd.Timestamp | None:
    later = index[index > date]
    return later[0] if len(later) else None


def run_backtest(prices: pd.DataFrame, universe: pd.DataFrame, config: StrategyConfig) -> BacktestResult:
    start, end = pd.Timestamp(config.start_date), pd.Timestamp(config.end_date)
    dates = prices.index[(prices.index >= start) & (prices.index <= end)]
    if dates.empty:
        raise ValueError("No prices fall inside the configured backtest period.")
    shares = pd.Series(0.0, index=prices.columns)
    cost_basis = pd.Series(0.0, index=prices.columns)
    cash = float(config.initial_capital)
    nav_rows: list[dict] = []
    holding_rows: list[dict] = []
    trade_rows: list[dict] = []
    sale_rows: list[dict] = []
    target_rows: list[dict] = []

    schedules: dict[pd.Timestamp, pd.Series] = {}
    for decision_date in monthly_decision_dates(prices.index, start, end):
        execution_date = _next_trading_date(prices.index, decision_date)
        if execution_date is None or execution_date > end:
            continue
        weights = target_weights(factor_scores(prices, decision_date, universe, config), config)
        schedules[execution_date] = weights

    for date in dates:
        px = prices.loc[date]
        if date in schedules:
            desired_weights = schedules[date]
            portfolio_value = cash + float((shares * px.fillna(0)).sum())
            desired_shares = pd.Series(0.0, index=prices.columns)
            desired_shares.loc[desired_weights.index] = portfolio_value * desired_weights / px.loc[desired_weights.index]
            # Sell first. Sales are executed at close minus the specified transaction cost.
            for ticker in prices.columns:
                quantity = max(shares[ticker] - desired_shares[ticker], 0.0)
                if quantity <= 1e-10:
                    continue
                gross = quantity * px[ticker]
                fee = gross * config.transaction_cost_rate
                proceeds = gross - fee
                basis = cost_basis[ticker] / shares[ticker] if shares[ticker] > 0 else 0.0
                realised = proceeds - basis * quantity
                shares[ticker] -= quantity
                cost_basis[ticker] -= basis * quantity
                cash += proceeds
                trade_rows.append({"date": date, "ticker": ticker, "side": "SELL", "quantity": quantity, "price": px[ticker], "gross_value": gross, "transaction_cost": fee})
                sale_rows.append({"date": date, "ticker": ticker, "realised_pnl": realised})
            # Scale all buys together so their fees can never make cash negative.
            deficits = (desired_shares - shares).clip(lower=0)
            desired_gross = float((deficits * px).sum())
            buy_scale = min(1.0, cash / (desired_gross * (1 + config.transaction_cost_rate))) if desired_gross else 0.0
            for ticker in prices.columns:
                quantity = deficits[ticker] * buy_scale
                if quantity <= 1e-10:
                    continue
                gross = quantity * px[ticker]
                fee = gross * config.transaction_cost_rate
                cash -= gross + fee
                shares[ticker] += quantity
                cost_basis[ticker] += gross + fee
                trade_rows.append({"date": date, "ticker": ticker, "side": "BUY", "quantity": quantity, "price": px[ticker], "gross_value": gross, "transaction_cost": fee})
            for ticker, weight in desired_weights.items():
                target_rows.append({"decision_date": date, "ticker": ticker, "target_weight": weight})

        value = cash + float((shares * px.fillna(0)).sum())
        nav_rows.append({"date": date, "nav": value, "cash": cash})
        current_value = shares * px
        for ticker, quantity in shares[shares > 1e-10].items():
            holding_rows.append({"date": date, "ticker": ticker, "shares": quantity, "market_value": current_value[ticker], "weight": current_value[ticker] / value})

    return BacktestResult(
        nav=pd.DataFrame(nav_rows).set_index("date")["nav"],
        holdings=pd.DataFrame(holding_rows),
        trades=pd.DataFrame(trade_rows),
        realised_sales=pd.DataFrame(sale_rows),
        targets=pd.DataFrame(target_rows),
    )
