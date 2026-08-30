from __future__ import annotations

import numpy as np
import pandas as pd

from .config import StrategyConfig


def monthly_decision_dates(index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    usable = index[(index >= start) & (index <= end)]
    periods = pd.Series(usable, index=usable).groupby(usable.to_period("M")).max()
    # A signal measured at a month-end is executed the next available price date.
    return list(periods.values)


def rebalance_dates(
    index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp, frequency: str
) -> list[pd.Timestamp]:
    """Return month-end or calendar-quarter-end decision dates."""
    dates = monthly_decision_dates(index, start, end)
    if frequency == "monthly":
        return dates
    if frequency == "quarterly":
        return [pd.Timestamp(date) for date in dates if pd.Timestamp(date).month in {3, 6, 9, 12}]
    raise ValueError(f"Unsupported rebalance frequency: {frequency}")


def eligible_tickers(universe: pd.DataFrame, date: pd.Timestamp) -> set[str]:
    relevant = universe[universe["effective_date"] <= date]
    if relevant.empty:
        return set()
    snapshot_date = relevant["effective_date"].max()
    return set(relevant.loc[relevant["effective_date"] == snapshot_date, "ticker"])


def _universe_membership(universe: pd.DataFrame, date: pd.Timestamp) -> pd.Series:
    """Return a ticker -> universe-label mapping from the latest snapshot."""
    relevant = universe[universe["effective_date"] <= date]
    if relevant.empty:
        return pd.Series(dtype=str)
    snapshot_date = relevant["effective_date"].max()
    snapshot = relevant[relevant["effective_date"] == snapshot_date]
    return snapshot.set_index("ticker")["universe"]


def _zscore(values: pd.Series) -> pd.Series:
    std = values.std(ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(0.0, index=values.index)
    return (values - values.mean()) / std


def _zscore_neutralized(values: pd.Series, groups: pd.Series) -> pd.Series:
    """Z-score within groups (e.g., size buckets) for sector/size-neutral ranking."""
    result = pd.Series(0.0, index=values.index)
    for group in groups.unique():
        mask = groups == group
        group_vals = values[mask]
        if len(group_vals) > 1:
            result[mask] = _zscore(group_vals)
    return result


def _estimate_betas(
    stock_prices: pd.DataFrame,
    benchmark: pd.Series,
    window: int,
) -> pd.Series:
    """Estimate trailing beta for each stock against the benchmark.

    Uses the trailing ``window`` daily returns ending at the last row of
    ``stock_prices``.  Returns a Series indexed by ticker.
    """
    stock_returns = stock_prices.pct_change().tail(window)
    bm_aligned = benchmark.reindex(stock_prices.index).ffill()
    bm_returns = bm_aligned.pct_change().tail(window)

    betas = pd.Series(1.0, index=stock_prices.columns)
    bm_vals = bm_returns.values
    bm_mean = np.nanmean(bm_vals)
    bm_var = np.nansum((bm_vals - bm_mean) ** 2)
    if bm_var <= 0:
        return betas
    for ticker in stock_prices.columns:
        stock_vals = stock_returns[ticker].values
        valid = np.isfinite(stock_vals) & np.isfinite(bm_vals)
        if valid.sum() < 20:
            continue
        sv = stock_vals[valid]
        bv = bm_vals[valid]
        bm_v = np.sum((bv - bv.mean()) ** 2)
        if bm_v > 0:
            betas[ticker] = np.sum((sv - sv.mean()) * (bv - bv.mean())) / bm_v
    return betas


def factor_scores(
    prices: pd.DataFrame,
    decision_date: pd.Timestamp,
    universe: pd.DataFrame,
    config: StrategyConfig,
    fundamentals: pd.DataFrame | None = None,
    benchmark: pd.Series | None = None,
) -> pd.DataFrame:
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

    # --- Residual momentum: strip out beta * benchmark return ---
    if config.use_residual_momentum and benchmark is not None:
        betas = _estimate_betas(recent, benchmark, window=min(required - 1, config.momentum_long_days))
        bm_aligned = benchmark.reindex(recent.index).ffill()
        bm_long_start = bm_aligned.iloc[-(config.momentum_long_days + 1)]
        bm_long_end = bm_aligned.iloc[-(config.momentum_skip_days + 1)]
        bm_short_start = bm_aligned.iloc[-(config.momentum_short_days + 1)]
        bm_end = bm_aligned.iloc[-1]
        bm_12_1_ret = bm_long_end / bm_long_start - 1
        bm_6_ret = bm_end / bm_short_start - 1
        factors["momentum_12_1"] = factors["momentum_12_1"] - betas * bm_12_1_ret
        factors["momentum_6"] = factors["momentum_6"] - betas * bm_6_ret

    if "quality_roe_debt" in config.signal_weights:
        if fundamentals is None:
            raise ValueError("quality_roe_debt requires dated fundamental data.")
        available = fundamentals.loc[fundamentals["reported_date"] <= decision_date]
        if available.empty:
            raise ValueError(f"No fundamentals were reported by {decision_date.date()}.")
        latest = available.drop_duplicates("ticker", keep="last").set_index("ticker")
        factors = factors.join(latest[["roe", "debt_to_equity"]], how="left")

    candidates = factors.index.intersection(list(eligible_tickers(universe, decision_date)))
    factors = factors.loc[candidates].dropna()
    factors = factors[factors["observations"] >= config.min_price_history_days]
    
    if factors.empty:
        return pd.DataFrame(columns=["score", "volatility"])
        
    if "quality_roe_debt" in config.signal_weights:
        factors["quality_roe_debt"] = _zscore(factors["roe"]) - _zscore(factors["debt_to_equity"])

    # --- Z-score: cross-sectional or neutralized within groups ---
    score = pd.Series(0.0, index=factors.index)
    if config.neutralize_by == "universe":
        membership = _universe_membership(universe, decision_date)
        groups = factors.index.map(membership).fillna("UNKNOWN")
        for name, weight in config.signal_weights.items():
            if name not in factors:
                raise ValueError(f"Signal {name!r} is not available in the factor data.")
            score += weight * _zscore_neutralized(factors[name], groups)
    else:
        for name, weight in config.signal_weights.items():
            if name not in factors:
                raise ValueError(f"Signal {name!r} is not available in the factor data.")
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


def apply_vol_target(
    weights: pd.Series,
    prices: pd.DataFrame,
    decision_date: pd.Timestamp,
    config: StrategyConfig,
) -> pd.Series:
    """Scale portfolio weights so ex-ante volatility matches target_volatility.

    If no target is configured or weights are empty, returns weights unchanged.
    The remaining allocation is held as cash by the backtest engine.
    """
    if config.target_volatility is None or weights.empty:
        return weights
    history = prices.loc[:decision_date]
    lookback = min(config.volatility_days, len(history) - 1)
    if lookback < 20:
        return weights
    returns = history[weights.index].pct_change().tail(lookback).dropna(how="all")
    if len(returns) < 20:
        return weights
    # Estimate ex-ante portfolio volatility using current weights
    port_returns = (returns.fillna(0) * weights).sum(axis=1)
    port_vol = float(port_returns.std() * np.sqrt(252))
    if port_vol <= 0:
        return weights
    scale = min(1.0, config.target_volatility / port_vol)
    return weights * scale
