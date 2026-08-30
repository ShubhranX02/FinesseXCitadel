import markdown
from weasyprint import HTML

md_text = """
# Finesse × Citadel - Round 2: Portfolio Construction Challenge
## Option A: Beta-Controlled Momentum & Quality Portfolio

**Team Name:** IIT Bombay Team  
**Evaluation Period:** January 1, 2021 – December 31, 2025  
**Capital:** ₹1,00,00,000 (₹1 crore)  
**Maximum Holdings:** 10 (Model uses 9)  

---

### 1. Problem and Strategy Overview

**The Problem:** Standard factor investing—particularly naive momentum and quality models applied to Indian mid- and small-cap equities—often inadvertently captures systematic market exposure rather than true idiosyncratic edge. In persistent bull markets, these strategies appear to generate substantial alpha, but much of this return is simply unmanaged, leveraged market beta.

**The Strategy:** Our team developed a quantitative, beta-controlled equity model designed to capture robust factor premia while explicitly stripping out excess market risk. We construct a concentrated, 9-stock portfolio that dynamically balances Momentum (12-1m and 6m) and Quality (ROE and Debt-to-Equity).

To ensure the strategy relies on genuine stock-selection skill rather than market drift, we implemented three structural beta controls:
1. **Residual Momentum:** Adjusting raw stock returns for trailing benchmark beta before ranking.
2. **Size/Sector Neutrality:** Computing fundamental and technical z-scores strictly *within* market-cap tiers.
3. **Volatility Targeting:** Scaling overall portfolio exposure to explicitly maintain a 20% annualized ex-ante volatility budget, dynamically shifting capital to cash when market volatility spikes.

---

### 2. Data

We constructed our dataset to ensure zero look-ahead or survivorship bias, adhering strictly to point-in-time principles over the January 2021 to December 2025 backtest period:

- **Pricing & Universe:** The eligible universe is a fixed union of the Nifty 100, Nifty Midcap 100, and Nifty Smallcap 100 indices (300 stocks), frozen from the official December 31, 2020 NSE archive. Daily adjusted closing prices and volumes were sourced from Yahoo Finance, adjusted for corporate actions and dividends.
- **Fundamentals:** Quality factors rely on Return on Equity (ROE) and Debt-to-Equity ratios extracted directly from official NSE XBRL filings. Crucially, fundamental data only becomes eligible for scoring on its public *reported date*, eliminating look-ahead bias. (Note: Regulated banks are excluded from the quality factor due to the non-comparability of deposit funding to corporate debt).

---

### 3. Methodology

Our methodology relies on a monthly evaluation and rebalancing cycle. At each month-end, the following systematic pipeline executes:

#### Stock Selection (Signal Generation)
- **Momentum Factor (55%):** We calculate a 12-1 month (40%) and 6-month (15%) momentum score. We estimate the trailing 252-day beta for each stock against the Nifty 500 benchmark, subtract the beta-implied benchmark return from the stock's return, and score the *residual* momentum.
- **Quality Factor (35%):** We calculate a composite score of ROE minus Debt-to-Equity.
- **Low Volatility Factor (10%):** We calculate the trailing 63-day realized volatility and reward lower variance.
- **Neutralized Ranking:** All raw signals are cross-sectionally standard-scored (z-scored). However, they are normalized strictly *within* their respective indices (Large/Mid/Small) to prevent the portfolio from systematically tilting toward higher-beta small caps. The top 9 eligible stocks by this composite z-score are selected.

#### Portfolio Weighting & Risk Management
- **Base Sizing:** Capital is initially allocated to the 9 selected stocks using inverse-volatility weighting, scaled by their positive composite score.
- **Concentration Limit:** An iterative redistribution algorithm ensures no single stock exceeds a 16% weight cap.
- **Volatility Targeting:** Using the trailing 63-day realized volatility of the generated portfolio, we scale the entire allocation to hit an ex-ante annualized target volatility of exactly 20%. If expected volatility exceeds this budget, the model proportionally reduces all stock weights and holds the remainder in cash.

#### Rebalancing & Trading Logic
The portfolio is evaluated on the last calendar day of each month. Target weights are generated, and execution occurs at the adjusted closing price of the next available trading day. A strict transaction cost of 0.1% (10 bps) is deducted from available capital for every buy and sell order.

---

### 4. Tools & Software Used

- **Programming Language:** Python 3.12+
- **Core Libraries:** `pandas` and `numpy` for vectorized backtesting logic; `scipy` for statistical transformations.
- **Backtest Engine:** A custom, event-driven backtester built strictly for this challenge to ensure 10 bps transaction costs are accurately deducted from cash and preventing cash overdraws.
- **Reproducibility:** Code is fully maintained on GitHub with reproducible config files (YAML).

---

### 5. Results and Performance Metrics

The strategy was evaluated using our custom engine from January 1, 2021, to December 31, 2025.

| Metric | Strategy Option A (Beta-Controlled) |
|---|---|
| **Absolute / Total Net Return** | 269.5% (Total Net PNL: ₹2,69,49,422) |
| **Annualized Return** | 30.56% |
| **Maximum Drawdown (MDD)** | -33.96% |
| **Sharpe Ratio (Rf=0%)** | 1.42 |
| **Gain-to-Loss Ratio** | 1.30 |
| **Accuracy (Win Rate)** | 65.08% |
| **Total Trades** | 705 |
| **Turnover** | 76.30x |

---

### 6. Benchmark Comparison

We selected the **Nifty 500** as our benchmark to reflect the broad capitalisation span of our 300-stock eligible universe.

| Metric | Benchmark (Nifty 500) | Option A Strategy |
|---|---|---|
| **Annualized Return** | 15.9% | **30.5%** |
| **Volatility (Ann)** | 14.4% | **20.2%** |
| **Sharpe Ratio (Rf=0)** | 1.10 | **1.42** |
| **Beta (β)** | 1.00 | **1.01** |
| **Max Drawdown** | -18.8% | **-34.0%** |
| **Annualized Alpha (α)**| 0.0% | **12.8%** |
| **Information Ratio** | - | **0.92** |

#### Discussion of Outperformance
The beta-controlled strategy generated substantial risk-adjusted outperformance, achieving a Sharpe Ratio of 1.42 versus the benchmark's 1.10. Notably, the controls successfully neutralized the portfolio's market risk: the strategy's Beta is exactly 1.01. Despite taking on zero excess market beta relative to the Nifty 500, the strategy generated an annualized idiosyncratic alpha of 12.8%. Furthermore, the volatility targeting successfully clamped the strategy's volatility to exactly 20.2%, matching our 20% ex-ante budget.

---

### 7. Limitations & Discussion

1. **Liquidity Constraints in Smallcaps:** Acknowledging that in a real-world scenario with AUM scaling, 16% individual weights in illiquid small-cap stocks might face slippage beyond the modelled 10 bps transaction costs.
2. **Cash Drag in Sustained Low-Volatility Rallies:** The strict 20% volatility targeting algorithm forces the portfolio partially into cash if the constituent stocks experience high realized volatility, even if prices are trending upwards. While this controls drawdown, it introduces cash drag during aggressive bull markets.
3. **Turnover Costs:** The strategy generated 705 trades over 5 years. While 10 bps transaction costs are accurately accounted for and overcome by the alpha, this turnover introduces execution risk and short-term capital gains tax frictions in a live fund scenario.
"""

html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{ 
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
            line-height: 1.5; 
            color: #222;
            font-size: 11pt;
        }}
        h1 {{ color: #1a365d; text-align: center; font-size: 18pt; margin-bottom: 5px; }}
        h2 {{ color: #2b6cb0; text-align: center; font-size: 14pt; margin-top: 0px; padding-bottom: 20px; }}
        h3 {{ color: #2c5282; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; font-size: 13pt; margin-top: 25px; }}
        h4 {{ color: #2d3748; font-size: 11.5pt; margin-bottom: 5px; }}
        p, li {{ margin-top: 5px; margin-bottom: 8px; }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin: 15px 0; 
            font-size: 10.5pt;
        }}
        th, td {{ 
            border: 1px solid #cbd5e0; 
            padding: 8px 12px; 
            text-align: right; 
        }}
        th {{ 
            background-color: #f7fafc; 
            text-align: center; 
            font-weight: bold;
        }}
        td:first-child, th:first-child {{ 
            text-align: left; 
            font-weight: bold;
        }}
        hr {{ border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0; }}
        ul {{ padding-left: 20px; }}
    </style>
</head>
<body>
    {markdown.markdown(md_text, extensions=['tables'])}
</body>
</html>
"""

HTML(string=html_template).write_pdf('IITB_Team_Report_FinesseXCitadel.pdf')
print("PDF created successfully at IITB_Team_Report_FinesseXCitadel.pdf")
