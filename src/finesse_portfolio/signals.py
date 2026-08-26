from __future__ import annotations

import numpy as np
import pandas as pd

from .config import StrategyConfig


def monthly_decision_dates(index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    usable = index[(index >= start) & (index <= end)]
    periods = pd.Series(usable, index=usable).groupby(usable.to_period("M")).max()
    # A signal measured at a month-end is executed the next available price date.
    return list(periods.values)


def eligible_tickers(universe: pd.DataFrame, date: pd.Timestamp) -> set[str]:
    relevant = universe[universe["effective_date"] <= date]
    if relevant.empty:
        return set()
    snapshot_date = relevant["effective_date"].max()
    return set(relevant.loc[relevant["effective_date"] == snapshot_date, "ticker"])


def _zscore(values: pd.Series) -> pd.Series:
    std = values.std(ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=values.index)
    return (values - values.mean()) / std


def factor_scores(prices: pd.DataFrame, decision_date: pd.Timestamp, universe: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    history = prices.loc[:decision_date]
    required = max(config.momentum_long_days, config.momentum_short_days, config.volatility_days) + 1
    if len(history) < required:
        return pd.DataFrame(columns=["score", "volatility"])
    recent = history.tail(required)
    long_start = recent.iloc[-(config.momentum_long_days + 1)]
    long_end = recent.iloc[-(config.momentum_skip_days + 1)]
    short_start = recent.iloc[-(config.momentum_short_days + 1)]
    end = recent.iloc[-1]
    volatility = recent.pct_change().tail(config.volatility_days).std(ddof=0) * np.sqrt(252)

    factors = pd.DataFrame(
        {
            "momentum_12_1": long_end / long_start - 1,
            "momentum_6": end / short_start - 1,
            "low_volatility": -volatility,
            "volatility": volatility,
            "observations": recent.notna().sum(),
        }
    )
    candidates = factors.index.intersection(list(eligible_tickers(universe, decision_date)))
    factors = factors.loc[candidates].dropna()
    factors = factors[factors["observations"] >= config.min_price_history_days]
    if factors.empty:
        return pd.DataFrame(columns=["score", "volatility"])
    score = pd.Series(0.0, index=factors.index)
    for name, weight in config.signal_weights.items():
        score += weight * _zscore(factors[name])
    factors["score"] = score
    return factors.sort_values("score", ascending=False)


def target_weights(scores: pd.DataFrame, config: StrategyConfig) -> pd.Series:
    selected = scores.head(config.holdings).copy()
    if selected.empty:
        return pd.Series(dtype=float)
    positive_score = selected["score"] - selected["score"].min() + 0.1
    raw = positive_score / selected["volatility"].clip(lower=0.05)
    weights = raw / raw.sum()
    # Iteratively cap and redistribute excess without exceeding the single-name limit.
    for _ in range(len(weights) + 1):
        excess = (weights - config.max_weight).clip(lower=0).sum()
        weights = weights.clip(upper=config.max_weight)
        free = weights < config.max_weight - 1e-12
        if excess < 1e-12 or not free.any():
            break
        weights.loc[free] += excess * weights.loc[free] / weights.loc[free].sum()
    return weights / weights.sum()
