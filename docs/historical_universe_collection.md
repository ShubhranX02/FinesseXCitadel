# Historical-universe collection protocol

## Goal

Construct a point-in-time universe for the union of Nifty 100, Nifty Midcap 100
and Nifty Smallcap 100. A stock is eligible only if it appears in the most recently
available complete snapshot on the signal date.

## Evidence hierarchy

1. Official NSE Indices constituent CSV downloaded on the historical effective date.
2. Official NSE archived daily/monthly report showing the complete constituent list.
3. Official NSE/NSE Indices reconstitution or corporate-action notice, used only to
   bridge between two validated complete snapshots.
4. Internet Archive capture of an official NSE constituent CSV, with capture timestamp
   recorded as the source URL.

Do not use personal GitHub repositories, current constituent lists, blog tables or a
stock's later index membership as a substitute for a historical source.

## Snapshot grid

Collect a complete 300-stock union snapshot at the earliest effective date on or before
each listed review date. If a corporate action changes one of the indices between two
reviews, collect the official notice and add a replacement snapshot from its effective
date.

| Period covered | Target snapshot date | Status |
| --- | --- | --- |
| 2021 Q1 | 2020-12-31 | Required |
| 2021 Q2 | 2021-03-31 | Required |
| 2021 Q3 | 2021-09-30 | Required |
| 2021 Q4 | 2021-12-31 | Required |
| 2022 H1 | 2022-03-31 | Required |
| 2022 H2 | 2022-09-30 | Required |
| 2023 H1 | 2023-03-31 | Required |
| 2023 H2 | 2023-09-29 | Required |
| 2024 H1 | 2024-03-28 | Required |
| 2024 H2 | 2024-09-27 | Required |
| 2025 H1 | 2025-03-28 | Required |
| 2025 H2 | 2025-09-30 | Required |

The dates are collection targets, not asserted official effective dates. Replace a
target with the effective date stated in the official notice and retain the notice URL.

## Required files per snapshot

For each date, obtain one complete official file for each index:

- Nifty 100 (100 constituents)
- Nifty Midcap 100 (100 constituents)
- Nifty Smallcap 100 (100 constituents)

Keep filenames as `YYYY-MM-DD_<index>.csv`. Do not edit them. Save the original file
outside Git, then import it using `scripts/import_constituent_snapshot.py`; that command
writes a normalised combined universe and its hash/source manifest.

## Public NSE archive shortcut

NSE's historical-report interface exposes a monthly **Indices – Market Capitalisation &
Weightage** ZIP archive. It is the preferred public raw source because one monthly file
may include constituent-level data for all required indices. The project can retrieve an
archive deterministically, for example:

```bash
python scripts/download_nse_market_cap_report.py --month 2021-03
```

The March 2021 archive URL resolved by the NSE interface is:

`https://www.niftyindices.com/Indices_-_Market_Capitalisation_and_Weightage/indices_dataMar2021.zip`

Before using a report, confirm that its contents include a complete 100-stock snapshot
for each of the three required indices. The next task is to automate this extraction;
until that validator passes, the archive is evidence—not backtest input.

The pipeline now performs a complete-coverage check. Download the monthly series, then
run the validator:

```bash
python scripts/download_nse_market_cap_report.py --start-month 2020-12 --end-month 2025-12
python scripts/build_nse_universe.py
```

It writes `data/nse_archive_coverage.csv` before refusing to change the production
universe if any archive is incomplete. The currently downloaded public archives contain
all three required constituent PDFs only through March 2022; from April 2022 onward,
they must not be treated as point-in-time constituent snapshots.

For a diagnostic extract of the complete archive portion only (never a production
2021–25 universe), use a separate output path:

```bash
python scripts/build_nse_universe.py --allow-incomplete \
  --output data/universe_history_archive_only.csv \
  --sources-output data/universe_sources_archive_only.csv
```

Post-March-2022 membership will instead be reconstructed from the official NSE Indices
change notices, starting from the last validated complete snapshot. Each add/remove and
its stated effective date must be entered in the change ledger, then reconciled to a
later complete source before the final backtest is run.

The ledger schema is versioned at `data/nse_index_change_ledger.csv`. It has one row per
official **ADD** or **REMOVE**, with the notice URL. The reconstruction command refuses
an empty ledger, verifies all three indices still contain exactly 100 names after each
notice date, and requires an explicit completeness declaration:

```bash
python scripts/reconstruct_nse_universe.py \
  --validated-through 2025-12-31
```

This produces the continuous `data/universe_history.csv` (complete archive history through
March 2022 plus reconstructed month-end history thereafter) and a notice-provenance file.
It is a candidate production input only after every applicable notice has been entered
and the ledger has been reconciled to an independent complete snapshot.

## Acceptance checks

Before a snapshot can be used in a backtest:

1. Each source file has exactly 100 unique NSE symbols.
2. The three files have no cross-index duplicate ticker.
3. Its source URL and SHA-256 hash appear in `data/universe_sources.csv`.
4. The effective date is no later than any decision date which uses it.
5. Any bridge created from a reconstitution notice is reconciled to the next complete
   snapshot: exactly 100 names remain in each index.

## Current known evidence

- An Internet Archive capture exists for the official Nifty 100 constituent CSV on
  8 August 2023. It is useful as a validation point, not a complete 2021–25 solution.
- NSE publishes historical index-level data and offers historical constituent data
  through its data service. The final report will state exactly which freely available
  snapshots/notices were used and any residual limitations.
