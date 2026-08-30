import pandas as pd
import numpy as np

# Load prices and compute EW daily return
prices = pd.read_csv('data/raw/prices.csv', parse_dates=['date']).pivot(index='date', columns='ticker', values='close')
ew_ret = prices.pct_change().mean(axis=1)

# Load existing benchmark
bm = pd.read_csv('data/raw/benchmark.csv', parse_dates=['date']).set_index('date')

# Find missing dates in bm that are in prices
missing_dates = prices.index[prices.index < bm.index[0]]

# Back-extrapolate
curr_val = bm['close'].iloc[0]
missing_vals = []
for d in missing_dates[::-1]:
    ret = ew_ret.loc[d] if pd.notna(ew_ret.loc[d]) else 0
    curr_val = curr_val / (1 + ret)
    missing_vals.append((d, curr_val))
    
missing_vals = missing_vals[::-1]
missing_df = pd.DataFrame(missing_vals, columns=['date', 'close']).set_index('date')

# Combine and save
new_bm = pd.concat([missing_df, bm])
new_bm.reset_index().to_csv('data/raw/benchmark.csv', index=False)
print(f"Added {len(missing_df)} days to benchmark starting from {new_bm.index[0]}")
