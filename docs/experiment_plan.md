# Predeclared experiment plan

## Research split

- **Development:** 1 January 2021–31 December 2024
- **Internal holdout:** 1 January 2025–31 December 2025
- **Competition out-of-sample:** 1 January 2026–30 June 2026 — never accessed while choosing the strategy.

The internal holdout is run only after the team chooses a candidate based on the development
period and diagnostic checks. We will not select a design merely because it has the highest
single-period total P&L.

## Candidate slate

These price-only strategies are defined before downloading/evaluating the dataset. All use the
permitted point-in-time universe, monthly signal measurement, next-trading-day execution, 10 bps
each way, long-only positions, and a 12–1 month momentum signal.

| Candidate | Holdings / cap | Signal blend | Economic rationale |
| --- | --- | --- | --- |
| `momentum_6` | 6 / 25% | 65% 12–1m momentum, 20% 6m momentum, 15% low volatility | Tests whether a higher-conviction trend portfolio compensates for concentration risk. |
| `momentum_8` | 8 / 20% | 55% 12–1m momentum, 25% 6m momentum, 20% low volatility | Balanced baseline: medium-term trend with position-level risk scaling. |
| `defensive_momentum_10` | 10 / 15% | 40% 12–1m momentum, 20% 6m momentum, 40% low volatility | Tests broader diversification and lower-volatility exposure. |

## Selection gates

A candidate can advance only if it:

1. Beats the broad benchmark on development-period Sharpe **and** has positive active return after costs.
2. Does not rely on a single stock for more than 30% of total P&L.
3. Has a materially lower maximum drawdown or meaningfully higher return than the other candidates; otherwise choose the simpler 8-stock baseline.
4. Has annual turnover and transaction costs consistent with a monthly strategy.
5. Remains credible under nearby, pre-specified sensitivity checks: 7/8/9 holdings and 15%/20% position caps for the selected blend.

## Fundamental factors

Quality and value may be tested only if we obtain a complete point-in-time fundamental dataset with
reporting-date lags. We will not use current ratios copied backward. If such a dataset is unavailable,
the final strategy remains price-only and says so plainly.

## How to run the split

```bash
# Development results
python scripts/run_backtest.py --config configs/research/momentum_8.yaml --end-date 2024-12-31

# One holdout run, after selection
python scripts/run_backtest.py --config configs/research/momentum_8.yaml --start-date 2025-01-01
```
