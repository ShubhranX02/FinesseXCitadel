# Finesse × Citadel — Round 2 Portfolio Construction

This repository implements a reproducible, long-only equity portfolio strategy for the
Finesse × Citadel Round 2 challenge. It is deliberately designed around transparent,
point-in-time portfolio rules rather than stock-specific hindsight.

## Strategy at a glance

- **Universe:** an organiser-approved fixed union of Nifty 100, Midcap 100 and
  Smallcap 100, frozen from the official 31 December 2020 NSE archive.
- **Signals:** 12–1 month momentum, six-month momentum and 63-trading-day realised
  volatility, cross-sectionally standardised on each decision date.
- **Selection:** the top eight eligible stocks by composite score.
- **Weights:** inverse-volatility weights, adjusted by positive composite score and
  capped at 20% per stock.
- **Execution:** the signal is measured at month-end and orders execute on the next
  available trading day. Every buy and sell is charged 10 bps.
- **Risk controls:** maximum 10 holdings, 20% single-name cap, minimum price history,
  and a monthly rebalance cadence to contain turnover.

This first baseline uses only prices and volume. It is the audit-friendly foundation for
controlled experiments with lagged point-in-time fundamentals later.

## Important data rules

Do not replace `data/universe_fixed.csv` with today's index constituents. The fixed
list is deliberately frozen from the 31 December 2020 official archive, as confirmed
permissible by the organiser. Prices must
be adjusted consistently for splits and dividends, and the initial download must include
at least 252 trading days before 1 January 2021 for signal warm-up.

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
python scripts/download_yahoo_data.py --universe data/universe_fixed.csv
python scripts/run_backtest.py --config configs/baseline.yaml
pytest
```

The downloader writes `data/raw/prices.csv` and `data/raw/benchmark.csv`. Run results
are written to `outputs/baseline/`.

The generated outputs include the equity curve, drawdown series, annual-return table,
complete order ledger, daily holdings, target weights, stock-level trade diagnostics,
benchmark curve, metrics JSON and a report-ready comparison chart.

## Input schemas

### `data/universe_fixed.csv`

| effective_date | ticker | universe |
| --- | --- | --- |
| 2020-12-31 | RELIANCE.NS | NIFTY_100 |

Each `effective_date` carries the same organiser-approved fixed list. The rows are
repeated only to provide explicit monthly coverage for the backtest. Use Yahoo-formatted
Indian tickers (`RELIANCE.NS`) if using the downloader.

### `data/raw/prices.csv`

| date | ticker | close | volume |
| --- | --- | ---: | ---: |
| 2020-01-02 | RELIANCE.NS | 1420.60 | 1234567 |

`close` must be an adjusted close if dividends are assumed reinvested. The pipeline
rejects duplicate ticker-date records and non-positive prices.

### `data/raw/benchmark.csv`

| date | close |
| --- | ---: |
| 2021-01-01 | 12345.67 |

Use a broad Nifty 500 total-return-equivalent series if accessible; otherwise document
the exact price-return benchmark and its limitations in the report.

## Repository layout

```
configs/        Frozen strategy assumptions
data/           Input schemas; raw market data remains untracked
scripts/        Download and run entry points
src/            Portfolio engine
tests/          Accounting and signal tests
outputs/        Generated metrics, equity curves and trades (untracked)
```

## Reproducibility checklist

1. Record data source URLs and download timestamp in the report.
2. Freeze the submitted config; do not tune it using January–June 2026 data.
3. Run `pytest` and preserve `outputs/baseline/metrics.json` with the submission.
4. State that execution is next-day adjusted close, and that 10 bps is charged per
   buy and per sell.
5. Include the commit hash used to generate report figures.

## Building the fixed competition universe

The production pipeline freezes the complete official 31 December 2020 snapshot. This
prevents a look-ahead in the source selection while complying with the organiser's
permission to use a fixed list:

```bash
python scripts/build_nse_universe.py --allow-incomplete \
  --output data/universe_history_archive_only.csv \
  --sources-output data/universe_sources_archive_only.csv
python scripts/freeze_fixed_universe.py
```

The freezer rejects incomplete or overlapping index snapshots and writes the original
source rows and a fixed-set hash to `data/universe_fixed_sources.csv`. See
`docs/assumption_register.md` for the confirmed rules. Point-in-time reconstruction
tools remain available for research, but are not part of the production backtest.

## Research discipline

The predeclared candidate models and 2021–24 development / 2025 internal-holdout protocol are
documented in `docs/experiment_plan.md`. This prevents result-driven parameter hunting and preserves
January–June 2026 as a true out-of-sample interval.
