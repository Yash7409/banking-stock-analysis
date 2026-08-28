"""
Financial Analytics & Quantitative Indicators Module for Banking Stocks.
Calculates returns, volatility, risk-adjusted metrics, technical indicators, and benchmark betas.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional


def compute_returns_and_growth(df: pd.DataFrame, price_col: str = "Close") -> pd.DataFrame:
    """
    Calculate daily returns, log returns, and cumulative returns.
    """
    res = df.copy()
    res["Daily_Return"] = res[price_col].pct_change()
    res["Log_Return"] = np.log(res[price_col] / res[price_col].shift(1))
    res["Cumulative_Return"] = (1 + res["Daily_Return"]).cumprod() - 1
    return res


def compute_technical_indicators(df: pd.DataFrame, price_col: str = "Close") -> pd.DataFrame:
    """
    Calculate SMA, EMA, RSI, MACD, Bollinger Bands, and ATR.
    """
    res = df.copy()
    close = res[price_col]

    # Moving Averages
    res["SMA_20"] = close.rolling(window=20).mean()
    res["SMA_50"] = close.rolling(window=50).mean()
    res["SMA_100"] = close.rolling(window=100).mean()
    res["SMA_200"] = close.rolling(window=200).mean()
    
    res["EMA_20"] = close.ewm(span=20, adjust=False).mean()
    res["EMA_50"] = close.ewm(span=50, adjust=False).mean()

    # Bollinger Bands (20 period, 2 std dev)
    rolling_mean_20 = close.rolling(window=20).mean()
    rolling_std_20 = close.rolling(window=20).std()
    res["BB_Middle"] = rolling_mean_20
    res["BB_Upper"] = rolling_mean_20 + (rolling_std_20 * 2)
    res["BB_Lower"] = rolling_mean_20 - (rolling_std_20 * 2)
    res["BB_Bandwidth"] = (res["BB_Upper"] - res["BB_Lower"]) / res["BB_Middle"]

    # RSI (14 period)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    
    # Exponential smoothing for RSI
    for i in range(14, len(res)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * 13 + gain.iloc[i]) / 14
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * 13 + loss.iloc[i]) / 14

    rs = avg_gain / avg_loss.replace(0, np.nan)
    res["RSI_14"] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    exp12 = close.ewm(span=12, adjust=False).mean()
    exp26 = close.ewm(span=26, adjust=False).mean()
    res["MACD"] = exp12 - exp26
    res["MACD_Signal"] = res["MACD"].ewm(span=9, adjust=False).mean()
    res["MACD_Hist"] = res["MACD"] - res["MACD_Signal"]

    # Average True Range (ATR 14)
    if "High" in res.columns and "Low" in res.columns:
        high = res["High"]
        low = res["Low"]
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        res["ATR_14"] = tr.rolling(window=14).mean()

    # Rolling Annualized Volatility (30-day and 90-day)
    if "Daily_Return" not in res.columns:
        res["Daily_Return"] = close.pct_change()
    res["Volatility_30D_Ann"] = res["Daily_Return"].rolling(window=30).std() * np.sqrt(252) * 100
    res["Volatility_90D_Ann"] = res["Daily_Return"].rolling(window=90).std() * np.sqrt(252) * 100

    # Drawdown calculations
    cumulative_max = close.cummax()
    res["Drawdown"] = (close - cumulative_max) / cumulative_max

    return res


def calculate_risk_return_metrics(
    df: pd.DataFrame,
    price_col: str = "Close",
    risk_free_rate: float = 0.065, # 6.5% standard Indian 10y G-Sec yield approx
    benchmark_df: Optional[pd.DataFrame] = None
) -> Dict[str, float]:
    """
    Calculate summary risk-return statistics:
    CAGR, Annualized Volatility, Sharpe Ratio, Sortino Ratio, Max Drawdown,
    VaR (95%), CVaR (95%), and Beta (relative to benchmark).
    """
    close = df[price_col].dropna()
    daily_returns = close.pct_change().dropna()
    
    if len(close) < 2:
        return {}

    # Total trading days & period in years
    trading_days = len(close)
    years = (close.index[-1] - close.index[0]).days / 365.25
    if years <= 0:
        years = trading_days / 252.0

    # CAGR
    start_val = close.iloc[0]
    end_val = close.iloc[-1]
    total_return = (end_val / start_val) - 1
    cagr = ((end_val / start_val) ** (1 / years)) - 1 if years > 0 else total_return

    # Annualized Volatility
    ann_volatility = daily_returns.std() * np.sqrt(252)

    # Sharpe Ratio
    excess_return = cagr - risk_free_rate
    sharpe_ratio = excess_return / ann_volatility if ann_volatility > 0 else np.nan

    # Sortino Ratio (Downside deviation relative to 0 or Rf/252)
    downside_returns = daily_returns[daily_returns < 0]
    downside_std_ann = downside_returns.std() * np.sqrt(252)
    sortino_ratio = excess_return / downside_std_ann if downside_std_ann > 0 else np.nan

    # Maximum Drawdown (MDD)
    cumulative_max = close.cummax()
    drawdown = (close - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()

    # Value at Risk (Historical 95% & 99% 1-day)
    var_95 = -np.percentile(daily_returns, 5)
    var_99 = -np.percentile(daily_returns, 1)

    # Conditional Value at Risk (Expected Shortfall at 95%)
    cvar_95 = -daily_returns[daily_returns <= -var_95].mean()

    # Beta and Alpha (relative to benchmark)
    beta = np.nan
    alpha = np.nan
    r_squared = np.nan
    if benchmark_df is not None:
        bench_close = benchmark_df[price_col].dropna()
        bench_returns = bench_close.pct_change().dropna()
        aligned = pd.concat([daily_returns, bench_returns], axis=1, join="inner").dropna()
        if len(aligned) > 20:
            stock_ret = aligned.iloc[:, 0]
            bench_ret = aligned.iloc[:, 1]
            cov = np.cov(stock_ret, bench_ret)[0][1]
            bench_var = np.var(bench_ret)
            if bench_var > 0:
                beta = cov / bench_var
                corr = np.corrcoef(stock_ret, bench_ret)[0][1]
                r_squared = corr ** 2
                # Annualized Jensen's Alpha
                bench_cagr = ((bench_close.iloc[-1] / bench_close.iloc[0]) ** (1 / years)) - 1
                alpha = cagr - (risk_free_rate + beta * (bench_cagr - risk_free_rate))

    # 52-week High / Low from data
    last_year_data = close.loc[close.index >= (close.index[-1] - pd.Timedelta(days=365))]
    high_52w = last_year_data.max() if len(last_year_data) > 0 else close.max()
    low_52w = last_year_data.min() if len(last_year_data) > 0 else close.min()
    current_price = close.iloc[-1]

    return {
        "Start Date": close.index[0].strftime("%Y-%m-%d"),
        "End Date": close.index[-1].strftime("%Y-%m-%d"),
        "Current Price (INR)": round(float(current_price), 2),
        "52-Week High (INR)": round(float(high_52w), 2),
        "52-Week Low (INR)": round(float(low_52w), 2),
        "Total Return (%)": round(float(total_return * 100), 2),
        "CAGR (%)": round(float(cagr * 100), 2),
        "Annualized Volatility (%)": round(float(ann_volatility * 100), 2),
        "Sharpe Ratio (Rf=6.5%)": round(float(sharpe_ratio), 2),
        "Sortino Ratio": round(float(sortino_ratio), 2),
        "Max Drawdown (%)": round(float(max_drawdown * 100), 2),
        "Historical VaR 95% (Daily %)": round(float(var_95 * 100), 2),
        "CVaR / Expected Shortfall 95% (%)": round(float(cvar_95 * 100), 2),
        "Beta (vs Bank Nifty)": round(float(beta), 2) if not np.isnan(beta) else "N/A",
        "Alpha (% Ann vs Bank Nifty)": round(float(alpha * 100), 2) if not np.isnan(alpha) else "N/A",
        "R-Squared (vs Bank Nifty)": round(float(r_squared), 2) if not np.isnan(r_squared) else "N/A"
    }


def compare_multiple_banks(
    data_dict: Dict[str, pd.DataFrame],
    benchmark_key: str = "^NSEBANK",
    risk_free_rate: float = 0.065
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate side-by-side comparison metrics table and correlation matrix.
    """
    bench_df = data_dict.get(benchmark_key)
    metrics_list = {}
    returns_series = {}

    for name, df in data_dict.items():
        if df.empty or "Close" not in df.columns:
            continue
        bench = bench_df if name != benchmark_key else None
        metrics = calculate_risk_return_metrics(df, risk_free_rate=risk_free_rate, benchmark_df=bench)
        metrics_list[name] = metrics
        returns_series[name] = df["Close"].pct_change()

    metrics_df = pd.DataFrame(metrics_list).T
    returns_df = pd.DataFrame(returns_series).dropna()
    corr_matrix = returns_df.corr()

    return metrics_df, corr_matrix
