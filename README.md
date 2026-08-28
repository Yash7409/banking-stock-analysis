# Banking Sector Historical Stock Analysis (HDFC Bank & SBI)

A quantitative analysis and interactive dashboard suite for evaluating the historical performance, risk metrics, technical indicators, and benchmark correlations of major Indian banks (**HDFC Bank**, **State Bank of India (SBI)**, **ICICI Bank**, **Kotak Mahindra Bank**, and **Axis Bank**) against the **Nifty Bank Index (`^NSEBANK`)** using Yahoo Finance data.

---

## 📁 Project Architecture

```
week one/
│
├── data_fetcher.py        # Yahoo Finance ingestion engine, OHLCV data cleaning & CSV persistence
├── bank_analysis.py       # Quantitative metrics (CAGR, Volatility, Sharpe, Sortino, VaR, CVaR, Beta, ATR, RSI, MACD)
├── visualizer.py          # Publication-grade chart generation (Matplotlib / Seaborn)
├── main.py                # End-to-end automated pipeline runner & summary report generator
├── app.py                 # Full-featured interactive Streamlit web dashboard
│
├── data/                  # Cleaned raw & processed datasets with indicators (CSV format)
│   ├── HDFCBANK_NS_historical_5y.csv
│   ├── SBIN_NS_historical_5y.csv
│   ├── ICICIBANK_NS_historical_5y.csv
│   ├── banks_combined_close_5y.csv
│   ├── banks_risk_return_comparison.csv
│   └── banks_returns_correlation_matrix.csv
│
└── output_charts/         # Generated high-resolution visualization charts (.png)
    ├── banking_sector_cumulative_growth.png
    ├── banking_sector_correlation_heatmap.png
    ├── hdfc_vs_sbi_volatility_and_drawdown.png
    ├── hdfc_price_and_volume_mas.png
    ├── hdfc_technical_indicators.png
    ├── hdfc_returns_distribution_var.png
    ├── sbi_price_and_volume_mas.png
    ├── sbi_technical_indicators.png
    └── sbi_returns_distribution_var.png
```

---

## ⚡ How to Run

### 1. Run the Full Automated Analysis Pipeline
To download the latest data, compute risk metrics, and generate all output charts:
```bash
python main.py
```

### 2. Launch the Interactive Streamlit Web App
To explore the interactive dashboard with candlesticks, customizable indicator overlays, and live bank comparisons:
```bash
streamlit run app.py
```

---

## 📊 Key Quantitative Findings (5-Year Horizon)

| Metric | HDFC Bank (`HDFCBANK.NS`) | State Bank of India (`SBIN.NS`) | ICICI Bank (`ICICIBANK.NS`) | Nifty Bank Index (`^NSEBANK`) |
| :--- | :--- | :--- | :--- | :--- |
| **Total Return (%)** | **-2.43%** | **+170.62%** | **+107.80%** | **+57.97%** |
| **CAGR (Ann. Return)** | **-0.49%** | **+22.06%** | **+15.77%** | **+9.59%** |
| **Annualized Volatility** | 20.90% | 24.61% | 20.16% | 16.99% |
| **Sharpe Ratio ($R_f=6.5\%$)** | -0.33 | **0.63** | 0.46 | 0.18 |
| **Sortino Ratio** | -0.46 | **0.86** | 0.69 | 0.24 |
| **Maximum Drawdown** | -28.64% | -23.94% | -22.33% | -20.91% |
| **1-Day Historical VaR (95%)**| 2.00% | 2.19% | 1.82% | 1.58% |
| **Beta (vs Bank Nifty)** | 0.96 | 1.07 | 0.93 | 1.00 |
| **Alpha (Annualized vs Index)**| -9.97% | **+12.25%** | +6.41% | 0.00% |

---

## 🧠 Insights & Comparative Analysis

1. **Growth Outperformance**:
   - **SBI (`SBIN.NS`)** delivered an exceptional **+170.62% total return** (22.06% CAGR) over the 5-year period, generating significant positive alpha (+12.25% annualized) against the Bank Nifty index.
   - **HDFC Bank (`HDFCBANK.NS`)** underperformed significantly post-merger integration challenges with flat/marginal negative return (-0.49% CAGR), lagging behind public and private peers.

2. **Risk & Volatility**:
   - SBI exhibited slightly higher annualized volatility (24.61%) compared to HDFC Bank (20.90%), but its superior returns yielded a robust **Sharpe ratio of 0.63** vs. HDFC Bank's **-0.33**.

3. **Drawdown Resilience**:
   - SBI recovered swiftly from drawdowns, keeping its maximum drawdown contained at **-23.94%**, whereas HDFC Bank experienced prolonged stagnation with a max drawdown of **-28.64%**.
