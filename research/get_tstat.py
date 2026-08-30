import pandas as pd
import numpy as np

# Load data
eq = pd.read_csv('outputs/beta_controlled_monthly/equity_curve.csv', parse_dates=['date']).set_index('date')
bm = pd.read_csv('outputs/beta_controlled_monthly/benchmark_equity_curve.csv', parse_dates=['date']).set_index('date')

df = pd.DataFrame({'nav': eq['nav'], 'bm': bm['benchmark_nav']}).dropna()
df['ret'] = df['nav'].pct_change()
df['bm_ret'] = df['bm'].pct_change()
df = df.dropna()

RF_ANNUAL = 0.06
RF_DAILY = (1 + RF_ANNUAL) ** (1/252) - 1

y = (df['ret'] - RF_DAILY).values
x = (df['bm_ret'] - RF_DAILY).values

n = len(x)
x_mean = np.mean(x)
y_mean = np.mean(y)

ss_x = np.sum((x - x_mean)**2)
ss_xy = np.sum((x - x_mean) * (y - y_mean))

beta = ss_xy / ss_x
alpha = y_mean - beta * x_mean

y_pred = alpha + beta * x
residuals = y - y_pred
rss = np.sum(residuals**2)
sigma_squared = rss / (n - 2)

se_alpha = np.sqrt(sigma_squared * (1/n + x_mean**2 / ss_x))
t_alpha = alpha / se_alpha

print(f"Alpha (Ann): {alpha * 252 * 100:.2f}%")
print(f"Alpha t-stat: {t_alpha:.2f}")
