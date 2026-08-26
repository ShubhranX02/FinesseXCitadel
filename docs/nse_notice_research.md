# NSE notice-reconstruction research log

## Current finding

The public **Indices – Market Capitalisation & Weightage** ZIP archive contains all
three required constituent PDFs for 16 monthly reports from 31 December 2020 through
31 March 2022. The 45 downloaded reports from April 2022 through December 2025 do not
contain those three files. `scripts/build_nse_universe.py` records this fact in
`data/nse_archive_coverage.csv` and refuses to overwrite a production universe.

This is not a permission to carry the March 2022 membership forward. The replacement
path is the official NSE Indices press-release archive, using the versioned
`data/nse_index_change_ledger.csv` and the reconstruction validator.

## Verified post-archive notices

These notices have been read against the original NSE Indices PDF. They are evidence
for individual ledger rows, not evidence that the ledger is already complete.

| Effective date | Affected challenge index | Official change | Source | Ledger status |
| --- | --- | --- | --- | --- |
| 2022-04-12 | Nifty Smallcap 100 | Remove `BEML`; add `BSE` | [NSE Indices release, 5 Apr 2022](https://www.niftyindices.com/Press_Release/ind_prs05042022_1.pdf) | Verified; do not enter into production ledger until every intervening notice is catalogued. |
| 2022-08-08 | Nifty 100 | Remove `NMDC`, `PEL`; add `LICI`, `TATAPOWER` | [NSE Indices release, 11 Jul 2022](https://www.niftyindices.com/Press_Release/ind_prs11072022.pdf) | Verified. |
| 2022-08-08 | Nifty Midcap 100 | Remove `TATAPOWER`; add `DELHIVERY` | [NSE Indices release, 11 Jul 2022](https://www.niftyindices.com/Press_Release/ind_prs11072022.pdf) | Verified. |
| 2022-09-30 | Nifty 100, Nifty Midcap 100, Nifty Smallcap 100 | Semi-annual reconstitution; the release contains explicit remove/add tables for all three challenge indices. | [NSE Indices release, 1 Sep 2022](https://www.niftyindices.com/Press_Release/ind_prs01092022.pdf) | Located; rows still to be transcribed and validated. |

The 2022-08-08 changes demonstrate why the reconstruction engine processes all
**REMOVE** rows before **ADD** rows at the same effective date: `TATAPOWER` moves from
Nifty Midcap 100 to Nifty 100 on that date.

## Completion rule

Before `data/nse_index_change_ledger.csv` can be passed to the reconstruction script
for a production universe, all of the following must be true:

1. Every NSE Indices release from April 2022 through December 2025 that affects any of
   the three challenge indices is classified as applicable or explicitly inapplicable.
2. Every applicable release is transcribed as matched `REMOVE`/`ADD` rows with its
   stated effective date and original URL.
3. The engine leaves exactly 100 unique securities in each challenge index after each
   effective date.
4. At least one later independently complete official snapshot reconciles to the
   reconstructed state, or the provenance limitation is explicitly disclosed and
   accepted by the organisers.

Until then, `data/nse_index_change_ledger.csv` remains deliberately empty and the
project will not produce a false 2022–25 backtest universe.
