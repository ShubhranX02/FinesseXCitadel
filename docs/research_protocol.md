# Research protocol

This file records the rules that protect the project from accidental overfitting.

## Data cut-off and split

Do not inspect or tune against January–June 2026, including when it is publicly
available. It is the competition stress-test interval.

Use 2021–2024 for development. Run 2025 exactly once as an internal holdout after
choosing a short list of candidate strategy families. Freeze the selected configuration
before submitting it for the competition out-of-sample test.

## Experiments

Every experiment must save:

- config file and Git commit hash;
- data snapshot date and source;
- 2021–24 and 2025 results separately;
- total return, annualised return, maximum drawdown, Sharpe, turnover, transaction
  costs, and benchmark comparison;
- a one-sentence rationale for keeping or rejecting it.

Keep the parameter grid modest. Parameters may be changed only for an economic or
implementation rationale, never merely because one setting had the highest historical
P&L.

## Strategy acceptance criteria

The final model must satisfy all of the following:

1. Uses no more than 10 names and only the permitted historical universe.
2. Charges 10 bps for every buy and sell, including the opening trade.
3. Uses only data available on the signal date; execution is the following trading day.
4. Has a clear benchmark comparison and interpretable risk controls.
5. Has no fragile dependency on one stock, one sector, or one year.
6. Can be reproduced from a fresh environment using the README instructions.
