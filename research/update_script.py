with open("generate_modern_pdf.py", "r") as f:
    content = f.read()

# Update the footnote
old_footnote = 'pdf.multi_cell(0, 5, "*Note: The Sharpe Ratio (1.42) is calculated using the daily arithmetic mean return, whereas the headline Annualized Return is geometric (CAGR). Alpha is also derived from daily arithmetic returns. This explains slight discrepancies if attempting simple mental arithmetic on the annualized summary figures.")'
new_footnote = 'pdf.multi_cell(0, 5, "*Note: Sharpe Ratio and Alpha are derived from daily arithmetic mean returns. For transparent reconciliation: Strategy Arithmetic Ann = 28.75%, Benchmark Arithmetic Ann = 15.81%, Risk-Free = 6.0%. Thus, Alpha = (28.75% - 6.0%) - 1.01 * (15.81% - 6.0%) = 12.8%. The headline 30.56% return is geometric (CAGR).")'
content = content.replace(old_footnote, new_footnote)

# Update the 2022 explanation under the YoY table
old_yoy_text = 'pdf.body_text("To demonstrate consistency across varied market regimes, the year-on-year returns are provided below:")'
new_yoy_text = 'pdf.body_text("To demonstrate consistency across varied market regimes, the year-on-year returns are provided below. Note the 2022 underperformance (-17.7% vs +3.0%): 2022 was characterized by a sharp macroeconomic regime change and significant momentum factor reversal. The strategy naturally suffered from this structural factor drawdown, which was then slightly exacerbated by our volatility-targeting cash drag triggering during the choppy market.")'
content = content.replace(old_yoy_text, new_yoy_text)

with open("generate_modern_pdf.py", "w") as f:
    f.write(content)
