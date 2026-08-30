# Finesse × Citadel — Round 2 Portfolio Construction

This repository implements a reproducible, beta-controlled equity portfolio strategy for the
Finesse × Citadel Round 2 challenge. It is designed around mathematically sound,
point-in-time portfolio rules, with a specific focus on neutralizing the excess market beta
typically associated with naive factor models in Indian mid/smallcaps.

## Strategy at a glance

- **Universe:** An organiser-approved fixed union of Nifty 100, Midcap 100 and
  Smallcap 100 (300 stocks), frozen from the official 31 December 2020 NSE archive.
- **Signals:** 
  - *Residual Momentum (12-1m and 6m):* Adjusted for trailing beta against the Nifty 500 to extract idiosyncratic momentum.
  - *Quality:* Point-in-time ROE and Debt-to-Equity, extracted from NSE XBRL filings with strict reporting-date awareness.
  - *Neutralization:* Z-scores are computed strictly *within* market-cap tiers (Large/Mid/Small) to ensure size/sector neutrality.
- **Selection:** The top 9 eligible stocks by composite score.
- **Weights & Risk Control:** 
  1. Base weights via inverse-volatility, adjusted by positive composite score and capped at 16% per stock.
  2. *Volatility Targeting:* The entire portfolio is scaled to explicitly maintain a 20% annualized ex-ante volatility budget, shifting to cash when the market becomes too erratic.
- **Execution:** Signals are measured at month-end and orders execute on the next
  available trading day's adjusted close. Every buy and sell is charged 10 bps (0.1%).

## Important data rules

Do not replace `data/universe_fixed.csv` with today's index constituents. The fixed
list is deliberately frozen from the 31 December 2020 official archive, as confirmed
permissible by the organiser. Prices and fundamentals are strictly point-in-time safe.

Raw data and generated outputs are ignored by Git. The repository retains schemas and
scripts, never opaque market-data dumps.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[download,dev]'

# Build the organiser-approved fixed universe from the downloaded NSE archive:
python scripts/build_nse_universe.py --allow-incomplete \
  --output data/universe_history_archive_only.csv \
  --sources-output data/universe_sources_archive_only.csv
python scripts/freeze_fixed_universe.py

# Download prices and scrape fundamentals:
python scripts/download_yahoo_data.py --universe data/universe_fixed.csv
# Note: scripts/build_fundamentals.py requires NSE archive scraping to be run first.

# Run the final beta-controlled backtest:
python scripts/run_backtest.py --config configs/beta_controlled_monthly.yaml
pytest
```

Run results are written to `outputs/beta_controlled_monthly/`.

The generated outputs include the equity curve, drawdown series, annual-return table,
complete order ledger, daily holdings, target weights, stock-level trade diagnostics,
benchmark curve, and the metrics JSON.

## Input schemas

### `data/universe_fixed.csv`
| effective_date | ticker | universe |
| --- | --- | --- |
| 2020-12-31 | RELIANCE.NS | NIFTY_100 |

### `data/raw/prices.csv`
| date | ticker | close | volume |
| --- | --- | ---: | ---: |
| 2020-01-02 | RELIANCE.NS | 1420.60 | 1234567 |

### `data/raw/nse_fundamentals.csv`
| ticker | period_end | reported_date | roe | debt_to_equity | equity |
| --- | --- | --- | ---: | ---: | ---: |
| RELIANCE.NS | 2021-03-31 | 2021-05-15 | 9.8 | 0.42 | 700000 |

### `data/raw/benchmark.csv`
| date | close |
| --- | ---: |
| 2021-01-01 | 12345.67 |

## Repository layout

```
configs/        Frozen strategy assumptions (YAML)
data/           Input schemas; raw market data remains untracked
scripts/        Download, pipeline, and backtest entry points
src/            Portfolio engine (signals, risk, sizing, execution)
tests/          Unit tests for accounting and signal fidelity
research/       Exploratory scripts and CAPM validation scripts
outputs/        Generated metrics, equity curves and trades (untracked)
```

## Reproducibility & Competition Guidelines

1. **Transaction Costs:** The engine accurately deducts 0.1% (10 bps) from available cash on every trade.
2. **Capital:** Strictly enforced at ₹1,00,00,000.
3. **Out-of-sample:** The config `beta_controlled_monthly.yaml` was frozen based strictly on 2021-2025 cross-validation. No parameters were tuned using the Jan-Jun 2026 holdout.
4. **Beta Control Validation:** The `research/validate_thesis.py` script contains the CAPM regressions used to prove that the beta controls successfully drop the portfolio beta from ~1.34 to ~1.01 compared to naive selection.
