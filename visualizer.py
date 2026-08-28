"""
Visualization Module for Banking Stocks Analysis.
Generates comprehensive static charts: Price Trends, Technicals, Risk-Return, and Comparative Heatmaps.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np

# Set styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8


def plot_price_and_volume_with_mas(
    df: pd.DataFrame,
    bank_name: str,
    ticker: str,
    output_path: str
):
    """
    Plot stock closing price with 20/50/200 SMA and trading volume bar chart.
    """
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 8), sharex=True,
        gridspec_kw={"height_ratios": [3, 1]}
    )

    # Price and Moving Averages
    ax1.plot(df.index, df["Close"], label="Close Price", color="#1f77b4", linewidth=1.8)
    if "SMA_50" in df.columns:
        ax1.plot(df.index, df["SMA_50"], label="50-Day SMA", color="#ff7f0e", linestyle="--", linewidth=1.2)
    if "SMA_200" in df.columns:
        ax1.plot(df.index, df["SMA_200"], label="200-Day SMA", color="#2ca02c", linestyle="-.", linewidth=1.4)
    if "BB_Upper" in df.columns and "BB_Lower" in df.columns:
        ax1.fill_between(df.index, df["BB_Lower"], df["BB_Upper"], color="#1f77b4", alpha=0.1, label="Bollinger Bands (20, 2σ)")

    ax1.set_title(f"{bank_name} ({ticker}) - Historical Price & Moving Averages", fontsize=14, fontweight="bold", pad=12)
    ax1.set_ylabel("Price (INR)", fontsize=11)
    ax1.legend(loc="upper left", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Volume Subplot
    colors = ["#2ca02c" if c >= o else "#d62728" for c, o in zip(df["Close"], df["Open"])]
    ax2.bar(df.index, df["Volume"] / 1e6, color=colors, alpha=0.7, width=1.0)
    ax2.set_ylabel("Volume (M)", fontsize=11)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.grid(True, linestyle="--", alpha=0.6)

    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=30)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_cumulative_growth_comparison(
    data_dict: dict,
    output_path: str,
    initial_investment: float = 10000.0
):
    """
    Plot normalized growth of ₹10,000 across multiple banks and benchmark index.
    """
    plt.figure(figsize=(14, 7))

    for name, df in data_dict.items():
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        growth = (close / close.iloc[0]) * initial_investment
        linestyle = "--" if "^" in name or "Index" in name else "-"
        linewidth = 2.4 if "HDFC" in name or "SBI" in name else 1.5
        plt.plot(growth.index, growth, label=f"{name} (Final: ₹{growth.iloc[-1]:,.0f})", linestyle=linestyle, linewidth=linewidth)

    plt.title(f"Growth of ₹{initial_investment:,.0f} Investment Over Time", fontsize=14, fontweight="bold", pad=12)
    plt.ylabel("Portfolio Value (INR)", fontsize=11)
    plt.xlabel("Date", fontsize=11)
    plt.legend(loc="upper left", frameon=True, fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=30)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_volatility_and_drawdowns(
    hdfc_df: pd.DataFrame,
    sbi_df: pd.DataFrame,
    output_path: str
):
    """
    Plot rolling 30-day annualized volatility and drawdown curves for HDFC Bank and SBI.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True)

    # Rolling Volatility
    if "Volatility_30D_Ann" in hdfc_df.columns:
        ax1.plot(hdfc_df.index, hdfc_df["Volatility_30D_Ann"], label="HDFC Bank (30D Ann. Vol %)", color="#1f77b4", linewidth=1.6)
    if "Volatility_30D_Ann" in sbi_df.columns:
        ax1.plot(sbi_df.index, sbi_df["Volatility_30D_Ann"], label="SBI (30D Ann. Vol %)", color="#ff7f0e", linewidth=1.6)
    ax1.set_title("30-Day Rolling Annualized Volatility (%)", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Volatility (%)", fontsize=11)
    ax1.legend(loc="upper left", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Drawdown
    if "Drawdown" in hdfc_df.columns:
        ax2.fill_between(hdfc_df.index, hdfc_df["Drawdown"] * 100, 0, color="#1f77b4", alpha=0.35, label="HDFC Bank Drawdown")
        ax2.plot(hdfc_df.index, hdfc_df["Drawdown"] * 100, color="#1f77b4", linewidth=1)
    if "Drawdown" in sbi_df.columns:
        ax2.fill_between(sbi_df.index, sbi_df["Drawdown"] * 100, 0, color="#ff7f0e", alpha=0.35, label="SBI Drawdown")
        ax2.plot(sbi_df.index, sbi_df["Drawdown"] * 100, color="#ff7f0e", linewidth=1)
    ax2.set_title("Underwater Historical Drawdown Curve (%)", fontsize=13, fontweight="bold")
    ax2.set_ylabel("Drawdown (%)", fontsize=11)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.legend(loc="lower left", frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.6)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=30)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_returns_distribution_and_var(
    df: pd.DataFrame,
    bank_name: str,
    output_path: str
):
    """
    Plot daily returns distribution, normal curve overlay, and VaR 95% & 99% cutoffs.
    """
    returns = df["Daily_Return"].dropna() * 100
    var_95 = np.percentile(returns, 5)
    var_99 = np.percentile(returns, 1)

    plt.figure(figsize=(12, 6))
    sns.histplot(returns, bins=70, kde=True, color="#1f77b4", stat="density", alpha=0.5, label="Daily Returns Distribution")
    
    # Overlay normal distribution
    mu, std = returns.mean(), returns.std()
    x = np.linspace(returns.min(), returns.max(), 200)
    p = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / std) ** 2)
    plt.plot(x, p, "k--", linewidth=1.5, label=f"Normal Fit (μ={mu:.2f}%, σ={std:.2f}%)")

    # VaR vertical lines
    plt.axvline(var_95, color="#d62728", linestyle="--", linewidth=1.8, label=f"95% 1-Day VaR: {abs(var_95):.2f}%")
    plt.axvline(var_99, color="#9467bd", linestyle=":", linewidth=2, label=f"99% 1-Day VaR: {abs(var_99):.2f}%")

    plt.title(f"{bank_name} - Daily Return Distribution & Risk (Value at Risk)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Daily Return (%)", fontsize=11)
    plt.ylabel("Density", fontsize=11)
    plt.legend(loc="upper right", frameon=True)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_technical_indicators_dashboard(
    df: pd.DataFrame,
    bank_name: str,
    output_path: str
):
    """
    Multi-panel technical dashboard:
    1. Price + Bollinger Bands
    2. RSI (14) with overbought/oversold boundaries
    3. MACD line, Signal line, and Histogram
    """
    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(14, 11), sharex=True,
        gridspec_kw={"height_ratios": [3, 1.2, 1.2]}
    )

    # Panel 1: Price and Bollinger Bands
    ax1.plot(df.index, df["Close"], label="Close Price", color="#1f77b4", linewidth=1.6)
    if "BB_Middle" in df.columns:
        ax1.plot(df.index, df["BB_Middle"], label="BB Middle (SMA 20)", color="#ff7f0e", linestyle="--")
        ax1.plot(df.index, df["BB_Upper"], label="BB Upper (+2σ)", color="#2ca02c", linestyle=":")
        ax1.plot(df.index, df["BB_Lower"], label="BB Lower (-2σ)", color="#d62728", linestyle=":")
        ax1.fill_between(df.index, df["BB_Lower"], df["BB_Upper"], color="gray", alpha=0.12)
    ax1.set_title(f"{bank_name} - Comprehensive Technical Analysis Dashboard", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Price (INR)", fontsize=11)
    ax1.legend(loc="upper left", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Panel 2: RSI
    if "RSI_14" in df.columns:
        ax2.plot(df.index, df["RSI_14"], label="RSI (14)", color="#8c564b", linewidth=1.5)
        ax2.axhline(70, color="#d62728", linestyle="--", linewidth=1.2, label="Overbought (70)")
        ax2.axhline(30, color="#2ca02c", linestyle="--", linewidth=1.2, label="Oversold (30)")
        ax2.fill_between(df.index, 30, 70, color="gray", alpha=0.08)
        ax2.set_ylabel("RSI", fontsize=11)
        ax2.set_ylim(10, 90)
        ax2.legend(loc="upper left", frameon=True)
        ax2.grid(True, linestyle="--", alpha=0.6)

    # Panel 3: MACD
    if "MACD" in df.columns:
        ax3.plot(df.index, df["MACD"], label="MACD Line (12, 26)", color="#1f77b4", linewidth=1.4)
        ax3.plot(df.index, df["MACD_Signal"], label="Signal Line (9)", color="#ff7f0e", linewidth=1.4)
        hist_colors = ["#2ca02c" if val >= 0 else "#d62728" for val in df["MACD_Hist"]]
        ax3.bar(df.index, df["MACD_Hist"], color=hist_colors, alpha=0.6, width=1.0, label="MACD Histogram")
        ax3.axhline(0, color="black", linestyle="--", linewidth=0.8)
        ax3.set_ylabel("MACD", fontsize=11)
        ax3.set_xlabel("Date", fontsize=11)
        ax3.legend(loc="upper left", frameon=True)
        ax3.grid(True, linestyle="--", alpha=0.6)

    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=30)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_correlation_heatmap(corr_df: pd.DataFrame, output_path: str):
    """
    Plot correlation matrix heatmap of daily returns among banking stocks.
    """
    plt.figure(figsize=(9, 7))
    sns.heatmap(
        corr_df,
        annot=True,
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        fmt=".2f",
        linewidths=1,
        cbar_kws={"label": "Pearson Correlation Coefficient"}
    )
    plt.title("Daily Returns Correlation Matrix - Indian Banking Sector", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
