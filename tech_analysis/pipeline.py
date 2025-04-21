import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime

def fetch_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    """
    Fetches historical stock data using yfinance.

    Args:
        ticker: The stock ticker symbol (e.g., "RELIANCE").
                Appends ".NS" for NSE stocks automatically.
        period: The period for which to fetch data (e.g., "1y", "2y", "max").

    Returns:
        A pandas DataFrame containing OHLCV data with lowercase column names.
    """
    data = yf.download(f"{ticker}.NS", period=period)
    data.columns = data.columns.str.lower() # Ensure lowercase columns
    return data

# Placeholder for cache_data function (Task 2.2)
def cache_data(data: pd.DataFrame, ticker: str) -> str:
    pass

# Placeholder for main execution flow (Task 5.1)
if __name__ == "__main__":
    pass
