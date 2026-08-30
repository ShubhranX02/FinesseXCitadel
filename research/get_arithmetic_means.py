import pandas as pd
import numpy as np

eq = pd.read_csv('outputs/beta_controlled_monthly/equity_curve.csv', parse_dates=['date']).set_index('date')
bm = pd.read_csv('outputs/beta_controlled_monthly/benchmark_equity_curve.csv', parse_dates=['date']).set_index('date')

df = pd.DataFrame({'nav': eq['nav'], 'bm': bm['benchmark_nav']}).dropna()
df['ret'] = df['nav'].pct_change()
df['bm_ret'] = df['bm'].pct_change()
df = df.dropna()

strat_arith_ann = df['ret'].mean() * 252 * 100
bm_arith_ann = df['bm_ret'].mean() * 252 * 100

print(f"Strategy Arithmetic Mean (Ann): {strat_arith_ann:.2f}%")
print(f"Benchmark Arithmetic Mean (Ann): {bm_arith_ann:.2f}%")
