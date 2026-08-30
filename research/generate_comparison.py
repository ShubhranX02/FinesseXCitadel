import json
import pandas as pd
import numpy as np

strategies = [
    'momentum_quality_quarterly',
    'momentum_quality_monthly',
    'momentum_only_quarterly',
    'quality_only_quarterly',
    'quality_65_momentum_35_quarterly'
]

def calc_regression(strat):
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
    
    return ann_alpha, beta, t_stat

results = []

for strat in strategies:
    with open(f"outputs/{strat}/metrics.json") as f:
        metrics = json.load(f)
    
    ann_alpha, beta, t_stat = calc_regression(strat)
    
    strat_name = strat.replace('_quarterly', ' (Q)').replace('_monthly', ' (M)').replace('momentum_', 'Mom_').replace('quality_', 'Qual_')
    if strat == 'quality_65_momentum_35_quarterly':
        strat_name = 'Qual_65_Mom_35 (Q)'
    
    results.append({
        'Strategy': strat_name,
        'Total Return': f"{metrics['total_return']*100:.2f}%",
        'Ann. Return': f"{metrics['annualised_return']*100:.2f}%",
        'MDD': f"{metrics['maximum_drawdown']*100:.2f}%",
        'Sharpe': f"{metrics['sharpe_ratio_rf_0']:.2f}",
        'Alpha (Ann)': f"{ann_alpha*100:.2f}%",
        'Beta': f"{beta:.2f}",
        'Alpha t-stat': f"{t_stat:.2f}",
        'Win Rate': f"{metrics['accuracy']*100:.2f}%" if metrics['accuracy'] else "N/A",
        'Gain/Loss': f"{metrics['gain_to_loss_ratio']:.2f}" if metrics['gain_to_loss_ratio'] else "N/A",
    })

# Add benchmark from the last metrics file
with open(f"outputs/{strategies[0]}/metrics.json") as f:
    metrics = json.load(f)
results.append({
    'Strategy': 'Benchmark (NIFTY_500)',
    'Total Return': f"{metrics['benchmark_total_return']*100:.2f}%",
    'Ann. Return': f"{metrics['benchmark_annualised_return']*100:.2f}%",
    'MDD': f"{metrics['benchmark_maximum_drawdown']*100:.2f}%",
    'Sharpe': f"{metrics['benchmark_sharpe_ratio_rf_0']:.2f}",
    'Alpha (Ann)': "N/A",
    'Beta': "1.00",
    'Alpha t-stat': "N/A",
    'Win Rate': "N/A",
    'Gain/Loss': "N/A",
})

columns = list(results[0].keys())
print("| " + " | ".join(columns) + " |")
print("| " + " | ".join(["---"] * len(columns)) + " |")
for row in results:
    print("| " + " | ".join(str(row[col]) for col in columns) + " |")

