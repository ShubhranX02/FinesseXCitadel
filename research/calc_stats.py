import pandas as pd
import numpy as np

def calc_stats(strat):
    eq = pd.read_csv(f"outputs/{strat}/equity_curve.csv", parse_dates=['date']).set_index('date')
    bm = pd.read_csv(f"outputs/{strat}/benchmark_equity_curve.csv", parse_dates=['date']).set_index('date')
    
    df = pd.merge(eq, bm, left_index=True, right_index=True)
    df['ret'] = df['nav'].pct_change()
    df['bm_ret'] = df['benchmark_nav'].pct_change()
    df = df.dropna()
    
    X = df['bm_ret'].values
    Y = df['ret'].values
    n = len(X)
    
    mean_x = np.mean(X)
    mean_y = np.mean(Y)
    
    cov_xy = np.sum((X - mean_x) * (Y - mean_y))
    var_x = np.sum((X - mean_x) ** 2)
    
    beta = cov_xy / var_x
    alpha = mean_y - beta * mean_x
    
    epsilon = Y - (alpha + beta * X)
    sigma_epsilon = np.sqrt(np.sum(epsilon ** 2) / (n - 2))
    
    se_alpha = sigma_epsilon * np.sqrt((1 / n) + (mean_x ** 2 / var_x))
    t_stat = alpha / se_alpha
    
    ann_alpha = alpha * 252
    
    print(f"| {strat} | {ann_alpha*100:.2f}% | {beta:.2f} | {t_stat:.2f} |")

print("| Strategy | Annualised Alpha | Beta | Alpha t-stat |")
print("| :--- | :--- | :--- | :--- |")
calc_stats('momentum_quality_quarterly')
calc_stats('momentum_quality_monthly')
