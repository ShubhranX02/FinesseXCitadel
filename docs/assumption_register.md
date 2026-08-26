# Assumption register

This register distinguishes confirmed competition rules from temporary implementation
choices. It must be updated whenever a decision changes; the report will reproduce all
material assumptions from this file.

| ID | Decision / assumption | Status | Rationale and consequence |
| --- | --- | --- | --- |
| A01 | Eligible securities are determined from the latest **point-in-time historical** constituent snapshot of Nifty 100, Nifty Midcap 100 and Nifty Smallcap 100. | Team decision; organiser confirmation pending | Prevents survivorship bias. Historical snapshots must be frozen and validated before a production run. |
| A02 | Transaction cost is 0.10% of gross notional on each buy and each sell, including the opening purchase. | Confirmed by team | The engine applies it separately to every execution. |
| A03 | Strategy is long-only, unlevered and starts fully invested except for cash left by transaction costs. | Provisional | This is the conservative default until organisers confirm whether shorts, leverage or strategic cash are allowed. |
| A04 | Signals are measured using the close on the last trading day of a month; orders execute at the next available trading day's adjusted close. | Provisional implementation convention | Avoids same-close look-ahead. The report will disclose this exact execution convention. |
| A05 | Adjusted close is used, treating splits and dividends as reflected in the price series. | Provisional data convention | Must match the chosen data vendor and benchmark methodology. |
| A06 | The baseline has eight holdings, a 20% single-name cap and monthly rebalancing. | Research baseline, not frozen | These are candidates to test on the development period only; they are not decisions made using 2026 data. |
| A07 | January–June 2026 is never used for feature design, parameter selection or model choice. | Team decision | It remains an untouched out-of-sample stress-test period. |
| A08 | Every universe snapshot is retained with its original source URL, local-file SHA-256 hash and validated 100-name count. | Implementation requirement | Makes the point-in-time membership evidence auditable and prevents silent data replacement. |
