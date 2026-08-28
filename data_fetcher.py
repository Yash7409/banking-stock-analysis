"""
Data Fetcher Module for Banking Stocks Analysis
Retrieves historical stock data from Yahoo Finance for major Indian banks.
"""

import os
import logging
from typing import List, Dict, Optional, Union
import pandas as pd
import yfinance as yf

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Default Major Indian Banks and Benchmarks (NSE Tickers)
DEFAULT_BANK_TICKERS = {
    "HDFC Bank": "HDFCBANK.NS",
    "State Bank of India (SBI)": "SBIN.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Axis Bank": "AXISBANK.NS",
    "Nifty Bank Index": "^NSEBANK"
}


def get_bank_info(ticker: str) -> Dict[str, Union[str, float, int]]:
    """
    Fetch company summary and metadata for a given ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "symbol": ticker,
            "shortName": info.get("shortName", ticker),
            "longName": info.get("longName", ticker),
            "currency": info.get("currency", "INR"),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"),
            "marketCap": info.get("marketCap", 0),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "trailingPE": info.get("trailingPE"),
            "dividendYield": info.get("dividendYield"),
            "sector": info.get("sector", "Financial Services"),
            "industry": info.get("industry", "Banks - Regional / Diversified"),
            "businessSummary": info.get("longBusinessSummary", "")
        }
    except Exception as e:
        logger.warning(f"Could not retrieve info for {ticker}: {e}")
        return {"symbol": ticker, "shortName": ticker}


def fetch_historical_data(
    ticker: str,
    period: str = "5y",
    interval: str = "1d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auto_adjust: bool = True
) -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a single ticker.

    Parameters:
    -----------
    ticker : str
        Ticker symbol (e.g., 'HDFCBANK.NS' or 'SBIN.NS')
    period : str
        Data period (e.g., '1y', '3y', '5y', '10y', 'max')
    interval : str
        Data interval ('1d', '1wk', '1mo')
    start_date : str, optional
        Start date 'YYYY-MM-DD'
    end_date : str, optional
        End date 'YYYY-MM-DD'
    auto_adjust : bool
        Whether to adjust OHLC automatically for stock splits/dividends

    Returns:
    --------
    pd.DataFrame
        Cleaned OHLCV dataframe with DatetimeIndex
    """
    logger.info(f"Fetching historical data for {ticker} (Period: {period}, Interval: {interval})...")
    
    stock = yf.Ticker(ticker)
    
    if start_date and end_date:
        df = stock.history(start=start_date, end=end_date, interval=interval, auto_adjust=auto_adjust)
    else:
        df = stock.history(period=period, interval=interval, auto_adjust=auto_adjust)
        
    if df.empty:
        # Fallback to yf.download if history returns empty
        logger.warning(f"history() returned empty dataframe for {ticker}, trying yf.download()...")
        df = yf.download(ticker, period=period, start=start_date, end=end_date, interval=interval, auto_adjust=auto_adjust)
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten multiindex if present
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    if df.empty:
        raise ValueError(f"No historical data found for {ticker}")

    # Standardize column names
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    
    # Remove timezone information to make dates uniform
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    # Standardize column naming
    rename_dict = {}
    for col in df.columns:
        if isinstance(col, tuple):
            clean_col = col[0].capitalize()
        else:
            clean_col = str(col).capitalize()
        rename_dict[col] = clean_col
    df.rename(columns=rename_dict, inplace=True)

    # Ensure required columns exist
    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in df.columns:
            if col.lower() in df.columns:
                df[col] = df[col.lower()]
            elif "Adj close" in df.columns and col == "Close":
                df["Close"] = df["Adj close"]

    # Filter out non-trading zero volume or NaN entries
    df = df.dropna(subset=["Close"])
    df = df[df["Close"] > 0]
    
    # Add ticker identifier column
    df["Ticker"] = ticker
    
    logger.info(f"Successfully fetched {len(df)} records for {ticker} from {df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}.")
    return df


def fetch_and_save_all_banks(
    tickers_dict: Optional[Dict[str, str]] = None,
    period: str = "5y",
    output_dir: str = "data"
) -> Dict[str, pd.DataFrame]:
    """
    Fetch historical data for multiple banks and save each as CSV in the output directory.
    Also produces a combined dataset of close prices.
    """
    if tickers_dict is None:
        tickers_dict = DEFAULT_BANK_TICKERS

    os.makedirs(output_dir, exist_ok=True)
    all_data = {}
    close_prices = {}

    for name, ticker in tickers_dict.items():
        try:
            df = fetch_historical_data(ticker=ticker, period=period)
            all_data[ticker] = df
            close_prices[name] = df["Close"]
            
            # Save individual CSV
            clean_name = ticker.replace("^", "").replace(".", "_")
            csv_path = os.path.join(output_dir, f"{clean_name}_historical_{period}.csv")
            df.to_csv(csv_path)
            logger.info(f"Saved {ticker} data to {csv_path}")
        except Exception as e:
            logger.error(f"Failed to fetch data for {name} ({ticker}): {e}")

    # Combine closing prices into a single dataframe
    if close_prices:
        combined_df = pd.DataFrame(close_prices).dropna()
        combined_path = os.path.join(output_dir, f"banks_combined_close_{period}.csv")
        combined_df.to_csv(combined_path)
        logger.info(f"Saved combined closing prices to {combined_path}")

    return all_data


if __name__ == "__main__":
    print("=== Testing Banking Stock Data Fetcher ===")
    data = fetch_and_save_all_banks(period="5y")
    print(f"\nSuccessfully downloaded data for {len(data)} tickers.")
    for ticker, df in data.items():
        print(f"\n[{ticker}] Summary:")
        print(df[["Open", "High", "Low", "Close", "Volume"]].tail(3))
