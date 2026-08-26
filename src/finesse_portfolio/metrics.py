from __future__ import annotations

import numpy as np
import pandas as pd


def performance_metrics(nav: pd.Series, initial_capital: float, realised_sales: pd.DataFrame) -> dict[str, float | int | None]:
    nav = nav.dropna()
    returns = nav.pct_change().dropna()
    years = len(returns) / 252
    total_return = nav.iloc[-1] / initial_capital - 1
    annualised_return = (nav.iloc[-1] / initial_capital) ** (1 / years) - 1 if years else np.nan
    drawdown = nav / nav.cummax() - 1
    daily_std = returns.std(ddof=0)
    sharpe = (returns.mean() / daily_std) * np.sqrt(252) if daily_std else np.nan
    metrics: dict[str, float | int | None] = {
        "initial_capital": initial_capital,
        "final_portfolio_value": float(nav.iloc[-1]),
        "total_net_pnl": float(nav.iloc[-1] - initial_capital),
        "total_return": float(total_return),
        "annualised_return": float(annualised_return),
        "maximum_drawdown": float(drawdown.min()),
        "sharpe_ratio_rf_0": float(sharpe),
    }
    if realised_sales.empty:
        metrics.update({"closed_sale_events": 0, "accuracy": None, "gain_to_loss_ratio": None})
        return metrics
    pnl = realised_sales["realised_pnl"]
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    metrics["closed_sale_events"] = len(pnl)
    metrics["accuracy"] = float((pnl > 0).mean())
    metrics["gain_to_loss_ratio"] = float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) else None
    return metrics
