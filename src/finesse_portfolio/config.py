from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class StrategyConfig:
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float
    transaction_cost_rate: float
    holdings: int
    max_weight: float
    min_price_history_days: int
    momentum_long_days: int
    momentum_skip_days: int
    momentum_short_days: int
    volatility_days: int
    signal_weights: dict[str, float]
    benchmark_name: str
    prices_path: str
    universe_path: str
    benchmark_path: str
    output_dir: str
    rebalance_frequency: str = "monthly"
    fundamentals_path: str | None = None
    use_residual_momentum: bool = False
    neutralize_by: str | None = None  # "universe" for size-neutral z-scoring
    target_volatility: float | None = None  # annual target, e.g. 0.20

    @classmethod
    def from_yaml(cls, path: str | Path) -> StrategyConfig:
        with Path(path).open() as handle:
            values = yaml.safe_load(handle)
        if values.get("rebalance_frequency", "monthly") not in {"monthly", "quarterly"}:
            raise ValueError("rebalance_frequency must be monthly or quarterly.")
        if not 1 <= values["holdings"] <= 10:
            raise ValueError("holdings must be between 1 and 10.")
        if not 0 < values["max_weight"] <= 1:
            raise ValueError("max_weight must be in (0, 1].")
        if values["holdings"] * values["max_weight"] < 1:
            raise ValueError("holdings × max_weight must be at least 1.")
        if sum(values["signal_weights"].values()) <= 0:
            raise ValueError("signal_weights must have a positive total.")
        if values.get("neutralize_by") not in {None, "universe"}:
            raise ValueError("neutralize_by must be None or 'universe'.")
        if values.get("target_volatility") is not None and values["target_volatility"] <= 0:
            raise ValueError("target_volatility must be positive.")
        return cls(
            **{
                name: values.get(name, field.default)
                for name, field in cls.__dataclass_fields__.items()
            }
        )
