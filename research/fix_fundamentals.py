import pandas as pd

cov = pd.read_csv('data/raw/nse_fundamentals_coverage.csv')
fund = pd.read_csv('data/raw/nse_fundamentals.csv')

# Find tickers/period_end where equity <= 0
bad = cov[cov['equity'] <= 0][['ticker', 'period_end']]

fund = fund.merge(bad.assign(bad_equity=True), on=['ticker', 'period_end'], how='left')
invalid_mask = fund['bad_equity'].fillna(False) | (fund['debt_to_equity'] < 0)

fund.loc[invalid_mask, ['roe', 'debt_to_equity']] = pd.NA
fund.drop(columns=['bad_equity'], inplace=True)

fund.to_csv('data/raw/nse_fundamentals.csv', index=False)
print(f"Fixed {invalid_mask.sum()} rows with invalid equity.")
