# Assumption register

This register distinguishes confirmed competition rules from temporary implementation
choices. It must be updated whenever a decision changes; the report will reproduce all
material assumptions from this file.

| ID | Decision / assumption | Status | Rationale and consequence |
| --- | --- | --- | --- |
| A01 | Eligible securities are the fixed union of Nifty 100, Nifty Midcap 100 and Nifty Smallcap 100 constituents in the official 31 December 2020 NSE archive. | Confirmed by organiser | The same 300-stock list is used for every 2021–25 decision date, as expressly permitted by the organiser. The source snapshot predates the backtest and is retained with a hash. |
| A02 | Transaction cost is 0.10% of gross notional on each buy and each sell, including the opening purchase. | Confirmed by organiser | The engine applies it separately to every execution. |
| A03 | Strategy is long-only, unlevered and starts fully invested except for cash left by transaction costs. | Provisional | This is the conservative default until organisers confirm whether shorts, leverage or strategic cash are allowed. |
| A04 | Signals are measured using the close on the last trading day of a month; orders execute at the next available trading day's adjusted close. | Provisional implementation convention | Avoids same-close look-ahead. The report will disclose this exact execution convention. |
| A05 | Adjusted close is used, treating splits and dividends as reflected in the price series. | Provisional data convention | Must match the chosen data vendor and benchmark methodology. |
| A06 | The baseline has eight holdings, a 20% single-name cap and monthly rebalancing. | Research baseline, not frozen | These are candidates to test on the development period only; they are not decisions made using 2026 data. |
| A07 | January–June 2026 is never used for feature design, parameter selection or model choice. | Team decision | It remains an untouched out-of-sample stress-test period. |
| A08 | The fixed-universe source snapshot is retained with its original source URL, local-file SHA-256 hash, 100-name-per-index validation and fixed-set hash. | Implementation requirement | Makes the permitted static membership choice auditable and prevents silent data replacement. |
| A09 | Review-date entries in `historical_universe_collection.md` are collection targets, not claims about official effective dates. | Documentation convention | The source notice controls the actual effective date recorded in the final universe file. |
| A10 | Point-in-time reconstruction is retained as research infrastructure but is not used by the production backtest. | Superseded by organiser confirmation | The public archive's post-March-2022 gaps no longer constrain the production universe because fixed membership is permitted. |
| A11 | The production universe is expanded into identical month-end snapshots solely to satisfy the backtest input contract; this does not represent historical index membership. | Implementation decision | It gives the strategy a deterministic, date-complete eligible set while preserving the organiser-approved fixed-list rule. |
