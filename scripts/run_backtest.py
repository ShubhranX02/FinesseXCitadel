from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from finesse_portfolio.backtest import run_backtest
from finesse_portfolio.config import StrategyConfig
from finesse_portfolio.data import load_benchmark, load_prices, load_universe, prices_to_wide
from finesse_portfolio.metrics import performance_metrics
from finesse_portfolio.reporting import annual_returns, drawdown_series, trade_diagnostics


def benchmark_nav(benchmark: pd.Series, config: StrategyConfig, dates: pd.DatetimeIndex) -> pd.Series:
    benchmark = benchmark.reindex(dates).ffill().dropna()
    return config.initial_capital * benchmark / benchmark.iloc[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen baseline backtest.")
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--start-date", help="Optional inclusive run start; does not change the saved config")
    parser.add_argument("--end-date", help="Optional inclusive run end; does not change the saved config")
    parser.add_argument("--output-dir", help="Optional output directory override")
    args = parser.parse_args()
    config = StrategyConfig.from_yaml(args.config)
    config = replace(
        config,
        start_date=args.start_date or config.start_date,
        end_date=args.end_date or config.end_date,
        output_dir=args.output_dir or config.output_dir,
    )
    prices = prices_to_wide(load_prices(config.prices_path))
    universe = load_universe(config.universe_path)
    result = run_backtest(prices, universe, config)
    benchmark = benchmark_nav(load_benchmark(config.benchmark_path), config, result.nav.index)
    metrics = performance_metrics(result.nav, config.initial_capital, result.realised_sales)
    benchmark_metrics = performance_metrics(benchmark, config.initial_capital, pd.DataFrame())
    metrics.update({f"benchmark_{key}": value for key, value in benchmark_metrics.items() if key not in {"initial_capital", "final_portfolio_value"}})
    metrics["benchmark_name"] = config.benchmark_name
    metrics["total_transaction_cost"] = float(result.trades["transaction_cost"].sum()) if not result.trades.empty else 0.0
    metrics["total_trades"] = len(result.trades)
    metrics["turnover"] = float(result.trades["gross_value"].sum() / config.initial_capital) if not result.trades.empty else 0.0

    output = Path(config.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result.nav.rename("nav").to_csv(output / "equity_curve.csv")
    drawdown_series(result.nav).to_csv(output / "drawdowns.csv")
    annual_returns(result.nav, config.initial_capital).to_csv(output / "annual_returns.csv", index=False)
    benchmark.rename("benchmark_nav").to_csv(output / "benchmark_equity_curve.csv")
    result.holdings.to_csv(output / "daily_holdings.csv", index=False)
    result.trades.to_csv(output / "trades.csv", index=False)
    trade_diagnostics(result.trades, config.initial_capital).to_csv(
        output / "stock_trade_statistics.csv", index=False
    )
    result.targets.to_csv(output / "target_weights.csv", index=False)
    with (output / "metrics.json").open("w") as handle:
        json.dump(metrics, handle, indent=2)
    plot = pd.concat([result.nav.rename("Strategy"), benchmark.rename(config.benchmark_name)], axis=1)
    ax = (plot / config.initial_capital).plot(figsize=(10, 5), title="Portfolio vs benchmark")
    ax.set_ylabel("Growth of ₹1")
    ax.figure.tight_layout()
    ax.figure.savefig(output / "portfolio_vs_benchmark.png", dpi=180)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
