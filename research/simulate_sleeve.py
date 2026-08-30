import pandas as pd
import numpy as np
import json

# Load equity curves
eq_qual = pd.read_csv("outputs/quality_only_quarterly/equity_curve.csv", parse_dates=['date']).set_index('date')
eq_mom = pd.read_csv("outputs/momentum_only_quarterly/equity_curve.csv", parse_dates=['date']).set_index('date')
bm = pd.read_csv("outputs/momentum_only_quarterly/benchmark_equity_curve.csv", parse_dates=['date']).set_index('date')

df = pd.DataFrame(index=eq_qual.index)
df['ret_qual'] = eq_qual['nav'].pct_change()
df['ret_mom'] = eq_mom['nav'].pct_change()
df['ret_bm'] = bm['benchmark_nav'].pct_change()
df = df.dropna()

# 35% Quality / 65% Momentum Daily Rebalanced Sleeve
df['ret_blend'] = 0.35 * df['ret_qual'] + 0.65 * df['ret_mom']
df['nav_blend'] = 10000000 * (1 + df['ret_blend']).cumprod()

# Metrics Calculation
total_return = (df['nav_blend'].iloc[-1] / 10000000) - 1
days = (df.index[-1] - df.index[0]).days
ann_return = (1 + total_return) ** (365.25 / days) - 1

roll_max = df['nav_blend'].cummax()
drawdown = (df['nav_blend'] - roll_max) / roll_max
mdd = drawdown.min()

sharpe = (df['ret_blend'].mean() / df['ret_blend'].std()) * np.sqrt(252)

# Regression for Alpha, Beta
X = df['ret_bm'].values
Y = df['ret_blend'].values
n = len(X)
mean_x, mean_y = np.mean(X), np.mean(Y)
cov_xy = np.sum((X - mean_x) * (Y - mean_y))
var_x = np.sum((X - mean_x) ** 2)
beta = cov_xy / var_x
alpha = mean_y - beta * mean_x
epsilon = Y - (alpha + beta * X)
sigma_epsilon = np.sqrt(np.sum(epsilon ** 2) / (n - 2))
se_alpha = sigma_epsilon * np.sqrt((1 / n) + (mean_x ** 2 / var_x))
t_stat = alpha / se_alpha
ann_alpha = alpha * 252

print(f"| 35% Qual / 65% Mom (Sleeve) | {total_return*100:.2f}% | {ann_return*100:.2f}% | {mdd*100:.2f}% | {sharpe:.2f} | {ann_alpha*100:.2f}% | {beta:.2f} | {t_stat:.2f} | N/A (Sleeve) | N/A (Sleeve) |")
