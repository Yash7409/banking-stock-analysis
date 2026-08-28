"""
Main Execution Script for Banking Historical Analysis Pipeline.
Fetches historical data, computes financial and quantitative metrics, generates charts,
and exports comprehensive summary reports.
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Local imports
from data_fetcher import fetch_historical_data, fetch_and_save_all_banks, DEFAULT_BANK_TICKERS, get_bank_info
from bank_analysis import (
    compute_returns_and_growth,
    compute_technical_indicators,
    calculate_risk_return_metrics,
    compare_multiple_banks
)
from visualizer import (
    plot_price_and_volume_with_mas,
    plot_cumulative_growth_comparison,
    plot_volatility_and_drawdowns,
    plot_returns_distribution_and_var,
    plot_technical_indicators_dashboard,
    plot_correlation_heatmap
)


def run_full_analysis(period: str = "5y", output_dir: str = "data", chart_dir: str = "output_charts"):
    """
    Execute end-to-end banking historical data analysis pipeline.
    """
    print("\n" + "="*80)
    print(f"🚀 INITIATING BANKING STOCKS HISTORICAL ANALYSIS PIPELINE (Period: {period})")
    print("="*80 + "\n")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(chart_dir, exist_ok=True)

    # 1. Fetch data for all banks
    print("📥 [Step 1/5] Fetching historical data from Yahoo Finance...")
    raw_data = fetch_and_save_all_banks(DEFAULT_BANK_TICKERS, period=period, output_dir=output_dir)

    # 2. Process data with indicators
    print("\n📊 [Step 2/5] Calculating technical indicators and risk metrics...")
    processed_data = {}
    for ticker, df in raw_data.items():
        processed_df = compute_returns_and_growth(df)
        processed_df = compute_technical_indicators(processed_df)
        processed_data[ticker] = processed_df
        
        # Save processed dataset
        clean_name = ticker.replace("^", "").replace(".", "_")
        proc_path = os.path.join(output_dir, f"{clean_name}_processed_{period}.csv")
        processed_df.to_csv(proc_path)

    # 3. Benchmark and cross-bank comparison
    print("\n📈 [Step 3/5] Performing comparative risk-return benchmarking...")
    named_processed_data = {}
    for name, ticker in DEFAULT_BANK_TICKERS.items():
        if ticker in processed_data:
            named_processed_data[name] = processed_data[ticker]

    metrics_df, corr_matrix = compare_multiple_banks(
        named_processed_data,
        benchmark_key="Nifty Bank Index",
        risk_free_rate=0.065
    )

    # Save metrics and correlation table
    metrics_path = os.path.join(output_dir, "banks_risk_return_comparison.csv")
    corr_path = os.path.join(output_dir, "banks_returns_correlation_matrix.csv")
    metrics_df.to_csv(metrics_path)
    corr_matrix.to_csv(corr_path)
    print(f" Saved metrics to {metrics_path}")
    print(f" Saved correlation matrix to {corr_path}")

    # 4. Generate Visualizations
    print("\n🎨 [Step 4/5] Generating publication-grade charts...")
    
    # HDFC Bank Charts
    hdfc_ticker = "HDFCBANK.NS"
    if hdfc_ticker in processed_data:
        hdfc_df = processed_data[hdfc_ticker]
        plot_price_and_volume_with_mas(
            hdfc_df, "HDFC Bank", hdfc_ticker,
            os.path.join(chart_dir, "hdfc_price_and_volume_mas.png")
        )
        plot_technical_indicators_dashboard(
            hdfc_df, "HDFC Bank",
            os.path.join(chart_dir, "hdfc_technical_indicators.png")
        )
        plot_returns_distribution_and_var(
            hdfc_df, "HDFC Bank",
            os.path.join(chart_dir, "hdfc_returns_distribution_var.png")
        )

    # SBI Charts
    sbi_ticker = "SBIN.NS"
    if sbi_ticker in processed_data:
        sbi_df = processed_data[sbi_ticker]
        plot_price_and_volume_with_mas(
            sbi_df, "State Bank of India (SBI)", sbi_ticker,
            os.path.join(chart_dir, "sbi_price_and_volume_mas.png")
        )
        plot_technical_indicators_dashboard(
            sbi_df, "State Bank of India (SBI)",
            os.path.join(chart_dir, "sbi_technical_indicators.png")
        )
        plot_returns_distribution_and_var(
            sbi_df, "State Bank of India (SBI)",
            os.path.join(chart_dir, "sbi_returns_distribution_var.png")
        )

    # Comparative Charts
    plot_cumulative_growth_comparison(
        named_processed_data,
        os.path.join(chart_dir, "banking_sector_cumulative_growth.png")
    )
    
    if hdfc_ticker in processed_data and sbi_ticker in processed_data:
        plot_volatility_and_drawdowns(
            processed_data[hdfc_ticker],
            processed_data[sbi_ticker],
            os.path.join(chart_dir, "hdfc_vs_sbi_volatility_and_drawdown.png")
        )

    plot_correlation_heatmap(
        corr_matrix,
        os.path.join(chart_dir, "banking_sector_correlation_heatmap.png")
    )

    # 5. Output Summary Report
    print("\n" + "="*80)
    print("📋 [Step 5/5] EXECUTIVE SUMMARY & KEY QUANTITATIVE FINDINGS")
    print("="*80 + "\n")
    print("--- RISK & RETURN COMPARISON TABLE ---")
    print(metrics_df.to_string())
    print("\n--- DAILY RETURNS CORRELATION MATRIX ---")
    print(corr_matrix.round(3).to_string())
    print("\n" + "="*80)
    print(f" Analysis completed successfully! All data files saved in '{output_dir}/' and charts in '{chart_dir}/'.")
    print("="*80 + "\n")

    return metrics_df, corr_matrix, processed_data


if __name__ == "__main__":
    run_full_analysis(period="5y")
